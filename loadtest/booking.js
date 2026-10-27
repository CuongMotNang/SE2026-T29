import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';
import {
  options as defaultOptions,
  queryAvailableSlots,
  slotsDuration,
  slotsSuccessRate,
  getTargetDate,
} from './slots.js';

/**
 * Main k6 load test script for the Booking system.
 * Reference: docs/devops/README.md (E15 load test requirement)
 */
export const options = {
  ...defaultOptions,
  thresholds: {
    ...defaultOptions.thresholds,
  },
};

export { slotsDuration, slotsSuccessRate };

export const bookingConflicts = new Counter('booking_conflicts');
export const bookingsCompleted = new Counter('bookings_completed');

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
const REQUEST_TIMEOUT = '10s';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function listSlots() {
  return queryAvailableSlots(BASE_URL);
}

export function createAndCancelBooking() {
  const { response, success } = queryAvailableSlots(BASE_URL, getTargetDate());
  if (!success) return;

  const slots = response.json();
  if (!check(slots, { 'booking has an available slot': (items) => items.length > 0 })) return;
  const slot = slots[Math.floor(Math.random() * slots.length)];
  const created = http.post(
    `${BASE_URL}/api/appointments`,
    JSON.stringify({ customer_name: `k6-${__VU}-${__ITER}`, starts_at: slot.starts_at }),
    {
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      tags: { name: 'POST /api/appointments' },
      timeout: REQUEST_TIMEOUT,
      redirects: 0,
      responseCallback: http.expectedStatuses(201, 409),
    }
  );
  check(created, { 'booking returns 201 or conflict 409': (res) => [201, 409].includes(res.status) });
  if (created.status === 409) {
    bookingConflicts.add(1);
    return;
  }
  if (created.status !== 201) return;

  let appointment;
  try {
    appointment = created.json();
  } catch (_err) {
    check(null, { 'created booking has a valid id': () => false });
    return;
  }
  if (!check(appointment, { 'created booking has a valid id': (item) => UUID.test(item?.id) })) return;

  // Only cancel the booking created by this iteration, never an existing booking.
  const cancelled = http.del(`${BASE_URL}/api/appointments/${appointment.id}`, null, {
    tags: { name: 'DELETE /api/appointments/:id' },
    timeout: REQUEST_TIMEOUT,
    redirects: 0,
    responseCallback: http.expectedStatuses(204),
  });
  if (check(cancelled, { 'booking cancellation returns 204': (res) => res.status === 204 })) {
    bookingsCompleted.add(1);
  }
}

export default createAndCancelBooking;
