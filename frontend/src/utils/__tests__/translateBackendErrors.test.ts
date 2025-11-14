/**
 * Tests for translateBackendErrors utility
 */
import { describe, it, expect, vi } from "vitest";
import { translateUsernameError } from "../translateBackendErrors";

describe("translateBackendErrors", () => {
  describe("translateUsernameError", () => {
    it("should translate known error messages", () => {
      const mockT = vi.fn((key: string, fallback: string) => {
        const translations: Record<string, string> = {
          "account.username.errors.cannotContainSpaces":
            "Le nom d'utilisateur ne peut pas contenir d'espaces.",
          "account.username.errors.empty":
            "Le nom d'utilisateur ne peut pas être vide.",
          "account.username.errors.tooShort":
            "Le nom d'utilisateur doit contenir au moins 3 caractères.",
          "account.username.errors.alreadyTaken":
            "Ce nom d'utilisateur est déjà pris.",
        };
        return translations[key] || fallback;
      });

      expect(
        translateUsernameError("Username cannot contain spaces.", mockT),
      ).toBe("Le nom d'utilisateur ne peut pas contenir d'espaces.");

      expect(translateUsernameError("Username cannot be empty.", mockT)).toBe(
        "Le nom d'utilisateur ne peut pas être vide.",
      );

      expect(
        translateUsernameError(
          "Username must be at least 3 characters long.",
          mockT,
        ),
      ).toBe("Le nom d'utilisateur doit contenir au moins 3 caractères.");

      expect(
        translateUsernameError("This username is already taken.", mockT),
      ).toBe("Ce nom d'utilisateur est déjà pris.");
    });

    it("should return original message for unknown errors", () => {
      const mockT = vi.fn((_key: string, fallback: string) => fallback);

      const unknownError = "Some unknown error message";
      expect(translateUsernameError(unknownError, mockT)).toBe(unknownError);
    });

    it("should handle all documented backend error messages", () => {
      const mockT = vi.fn((_key: string, fallback: string) => fallback);

      const backendErrors = [
        "Username cannot be empty.",
        "Username must be at least 3 characters long.",
        "Username must be at most 100 characters long.",
        "Username must start with a letter or number.",
        "Username cannot contain spaces.",
        "Username can only contain letters, numbers, underscores, and hyphens.",
        "This username is already taken.",
      ];

      backendErrors.forEach((error) => {
        const result = translateUsernameError(error, mockT);
        expect(result).toBeTruthy();
        expect(mockT).toHaveBeenCalled();
      });
    });
  });
});
