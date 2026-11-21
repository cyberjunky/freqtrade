/**
 * Test setup: pin the default locale to en-US.
 *
 * The formatters intentionally follow the user's locale (decimal comma on e.g.
 * nl-NL systems). The assertions in the unit tests are written for en-US, so the
 * default locale is pinned here to make the tests independent of the machine.
 */
const TEST_LOCALE = 'en-US';

const origNumberToLocaleString = Number.prototype.toLocaleString;
Number.prototype.toLocaleString = function (
  this: number,
  locales?: Intl.LocalesArgument,
  options?: Intl.NumberFormatOptions,
) {
  const useDefault = locales === undefined || locales === 'fullwide';
  return origNumberToLocaleString.call(this, useDefault ? TEST_LOCALE : locales, options);
};

const OrigDateTimeFormat = Intl.DateTimeFormat;
function PinnedDateTimeFormat(
  locales?: Intl.LocalesArgument,
  options?: Intl.DateTimeFormatOptions,
) {
  return new OrigDateTimeFormat(locales ?? TEST_LOCALE, options);
}
PinnedDateTimeFormat.prototype = OrigDateTimeFormat.prototype;
PinnedDateTimeFormat.supportedLocalesOf = OrigDateTimeFormat.supportedLocalesOf;
Intl.DateTimeFormat = PinnedDateTimeFormat as typeof Intl.DateTimeFormat;
