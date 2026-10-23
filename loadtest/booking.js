import { sleep } from 'k6';
import {
  options as defaultOptions,
  queryAvailableSlots,
  slotsDuration,
  slotsSuccessRate,
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

export default function () {
  queryAvailableSlots();
  sleep(1);
}
