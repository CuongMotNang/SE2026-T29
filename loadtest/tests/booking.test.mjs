import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const id = '11111111-1111-4111-8111-111111111111';
const slot = { starts_at: '2099-11-02T10:00:00+07:00' };
const response = (status, body) => ({
  status, body: JSON.stringify(body),
  json() { return JSON.parse(this.body); },
});

async function loadBooking(responses, env = {}) {
  const calls = [];
  const checks = [];
  const metrics = {};
  const context = vm.createContext({ __ENV: env, __VU: 1, __ITER: 0, console });
  class Metric {
    constructor(name) { this.name = name; metrics[name] = []; }
    add(value) { metrics[this.name].push(value); }
  }
  const request = (method, url, body, params) => {
    calls.push({ method, url, body, params });
    assert.ok(responses.length, `Unexpected ${method} ${url}`);
    return responses.shift();
  };
  const http = {
    get: (url, params) => request('GET', url, null, params),
    post: (url, body, params) => request('POST', url, body, params),
    del: (url, body, params) => request('DELETE', url, body, params),
    expectedStatuses: (...statuses) => statuses,
  };
  const definitions = {
    'k6/http': { default: http },
    k6: {
      check: (value, predicates) => {
        const results = Object.entries(predicates).map(([name, fn]) => {
          const ok = Boolean(fn(value));
          checks.push({ name, ok });
          return ok;
        });
        return results.every(Boolean);
      },
      sleep: () => assert.fail('Arrival-rate scenarios must not sleep'),
    },
    'k6/metrics': { Counter: Metric, Rate: Metric, Trend: Metric },
  };
  const modules = new Map();
  for (const [name, exports] of Object.entries(definitions)) {
    modules.set(name, new vm.SyntheticModule(Object.keys(exports), function () {
      for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
    }, { context }));
  }
  for (const name of ['slots.js', 'booking.js']) {
    modules.set(`./${name}`, new vm.SourceTextModule(
      await readFile(new URL(`../${name}`, import.meta.url), 'utf8'), { context }
    ));
  }
  const module = modules.get('./booking.js');
  await module.link((name) => {
    assert.ok(modules.has(name), `Unexpected import: ${name}`);
    return modules.get(name);
  });
  await module.evaluate();
  return { script: module.namespace, calls, checks, metrics };
}

test('queries slots, creates and cancels only its own booking', async () => {
  const run = await loadBooking([
    response(200, [slot]), response(201, { id }), response(204, null),
  ], { BASE_URL: 'http://demo:8000/', TARGET_DATE: '2099-11-02' });
  run.script.createAndCancelBooking();
  assert.deepEqual(run.calls.map((call) => call.method), ['GET', 'POST', 'DELETE']);
  assert.equal(run.calls[0].url, 'http://demo:8000/api/slots?date=2099-11-02');
  assert.deepEqual(JSON.parse(run.calls[1].body), { customer_name: 'k6-1-0', ...slot });
  assert.equal(run.calls[2].url, `http://demo:8000/api/appointments/${id}`);
  assert.equal(run.calls[2].params.tags.name, 'DELETE /api/appointments/:id');
  assert.ok(run.checks.every((check) => check.ok));
  assert.deepEqual(run.metrics.bookings_completed, [0, 1]);
  assert.deepEqual(run.metrics.http_server_errors, [false, false, false]);
});

test('409 is an expected conflict and never triggers cancellation', async () => {
  const run = await loadBooking([response(200, [slot]), response(409, { detail: 'Booked' })]);
  run.script.default();
  assert.equal(run.calls.length, 2);
  assert.ok(run.calls[1].params.responseCallback.includes(409));
  assert.deepEqual(run.metrics.booking_conflicts, [0, 1]);
  assert.deepEqual(run.metrics.bookings_completed, [0]);
  assert.deepEqual(run.metrics.http_server_errors, [false, false]);
});

test('default arrival profiles target 10 HTTP requests/s for 10 minutes', async () => {
  const { script } = await loadBooking([]);
  const { slots, booking } = script.options.scenarios;
  assert.equal(slots.executor, 'constant-arrival-rate');
  assert.equal(booking.executor, 'constant-arrival-rate');
  assert.equal(slots.exec, 'listSlots');
  assert.equal(booking.exec, 'createAndCancelBooking');
  assert.equal(slots.timeUnit, '5s');
  assert.equal(booking.timeUnit, '5s');
  assert.equal((slots.rate + booking.rate * 3) / 5, 10);
  assert.equal(slots.duration, '10m');
  assert.equal(booking.duration, '10m');
  assert.equal(booking.gracefulStop, '45s');
  assert.equal(booking.preAllocatedVUs, 10);
  assert.equal(booking.maxVUs, 50);
  assert.equal(script.options.vus, undefined);
  assert.equal(script.options.duration, undefined);
});

test('arrival rate, duration and VU allocation are configurable', async () => {
  const { script } = await loadBooking([], {
    TARGET_RPS: '5', DURATION: '5s', PRE_ALLOCATED_VUS: '2', MAX_VUS: '4',
  });
  const { slots, booking } = script.options.scenarios;
  assert.equal((slots.rate + booking.rate * 3) / 5, 5);
  assert.equal(booking.duration, '5s');
  assert.equal(booking.preAllocatedVUs, 2);
  assert.equal(booking.maxVUs, 4);
});

for (const env of [
  { TARGET_RPS: '0' }, { TARGET_RPS: '-1' }, { TARGET_RPS: '1.5' },
  { TARGET_RPS: 'invalid' }, { PRE_ALLOCATED_VUS: '0' }, { MAX_VUS: '1' },
]) {
  test(`rejects invalid arrival configuration ${JSON.stringify(env)}`, async () => {
    await assert.rejects(loadBooking([], env), /positive integer|MAX_VUS must be/);
  });
}

for (const [name, responses] of [
  ['empty slots', [response(200, [])]],
  ['invalid slots JSON', [{ status: 200, body: 'invalid' }]],
  ['failed slots request', [response(500, {})]],
  ['invalid slot shape', [response(200, [{ id }])]],
  ['failed create', [response(200, [slot]), response(500, {})]],
  ['missing booking id', [response(200, [slot]), response(201, {})]],
  ['unsafe booking id', [response(200, [slot]), response(201, { id: '../existing' })]],
  ['invalid create JSON', [response(200, [slot]), { status: 201, json() { throw Error(); } }]],
  ['failed cancellation', [response(200, [slot]), response(201, { id }), response(500, {})]],
]) {
  test(`${name} records failed checks without claiming a completed booking`, async () => {
    const run = await loadBooking(responses);
    run.script.createAndCancelBooking();
    assert.ok(run.checks.some((check) => !check.ok));
    assert.deepEqual(run.metrics.bookings_completed, [0]);
    if (['failed slots request', 'failed create', 'failed cancellation'].includes(name)) {
      assert.equal(run.metrics.http_server_errors.filter(Boolean).length, 1);
    }
    if (name !== 'failed cancellation') {
      assert.ok(run.calls.every((call) => call.method !== 'DELETE'));
    }
  });
}

test('E15 thresholds cover latency per route, errors, checks and insufficient load', async () => {
  const { script } = await loadBooking([]);
  const thresholds = JSON.parse(JSON.stringify(script.options.thresholds));
  for (const route of ['GET /api/slots', 'POST /api/appointments', 'DELETE /api/appointments/:id']) {
    assert.deepEqual(thresholds[`http_req_duration{name:${route}}`], ['p(95)<500']);
  }
  assert.deepEqual(thresholds.http_req_duration, ['p(95)<500']);
  assert.deepEqual(thresholds.http_req_failed, ['rate<0.01']);
  assert.deepEqual(thresholds.http_server_errors, ['rate<0.01']);
  assert.deepEqual(thresholds.checks, ['rate>0.99']);
  assert.deepEqual(thresholds.bookings_completed, ['count>0']);
  assert.deepEqual(thresholds.dropped_iterations, ['count==0']);
});
