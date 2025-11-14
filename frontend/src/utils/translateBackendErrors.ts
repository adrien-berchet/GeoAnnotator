/**
 * Utility functions to translate backend error messages to localized strings
 */

type TranslateFunction = (key: string, fallback: string) => string;

/**
 * Translates backend username validation error messages to localized strings
 * @param error - The error message from the backend
 * @param t - The translation function from useLanguage hook
 * @returns The translated error message
 */
export function translateUsernameError(
  error: string,
  t: TranslateFunction,
): string {
  const errorMap: Record<string, string> = {
    "Username cannot be empty.": t(
      "account.username.errors.empty",
      "Username cannot be empty.",
    ),
    "Username must be at least 3 characters long.": t(
      "account.username.errors.tooShort",
      "Username must be at least 3 characters long.",
    ),
    "Username must be at most 100 characters long.": t(
      "account.username.errors.tooLong",
      "Username must be at most 100 characters long.",
    ),
    "Username must start with a letter or number.": t(
      "account.username.errors.mustStartWithAlphanumeric",
      "Username must start with a letter or number.",
    ),
    "Username cannot contain spaces.": t(
      "account.username.errors.cannotContainSpaces",
      "Username cannot contain spaces.",
    ),
    "Username can only contain letters, numbers, underscores, and hyphens.": t(
      "account.username.errors.invalidCharacters",
      "Username can only contain letters, numbers, underscores, and hyphens.",
    ),
    "This username is already taken.": t(
      "account.username.errors.alreadyTaken",
      "This username is already taken.",
    ),
  };

  return errorMap[error] || error;
}
