import { expect, test } from "@playwright/test";
import { dateInBookingZone, openDay, slotList } from "./helpers";

test("hiển thị danh sách slot trống cho ngày đã chọn", async ({ page }) => {
  await openDay(page, dateInBookingZone(3));

  const slots = slotList(page).getByRole("button");
  await expect(slots.first()).toBeVisible();
  expect(await slots.count()).toBeGreaterThan(0);
});

test("đổi ngày thì tải lại danh sách slot", async ({ page }) => {
  await openDay(page, dateInBookingZone(4));
  const slotCountForFirstDay = await slotList(page).getByRole("button").count();

  await page.getByLabel("Ngày").fill(dateInBookingZone(5));
  await expect(slotList(page).getByRole("button").first()).toBeVisible();

  expect(slotCountForFirstDay).toBeGreaterThan(0);
  expect(await slotList(page).getByRole("button").count()).toBeGreaterThan(0);
});
