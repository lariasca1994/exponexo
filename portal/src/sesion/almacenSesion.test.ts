import { afterEach, describe, expect, it } from "vitest";
import { getInMemoryTokens, setInMemoryTokens } from "./almacenSesion";

describe("session token storage", () => {
  afterEach(() => {
    setInMemoryTokens(null, null);
  });

  it("keeps access and refresh tokens in memory", () => {
    setInMemoryTokens("access-token", "refresh-token");

    expect(getInMemoryTokens()).toEqual({
      accessToken: "access-token",
      refreshToken: "refresh-token",
    });
  });

  it("clears both tokens when the session is cleared", () => {
    setInMemoryTokens("access-token", "refresh-token");
    setInMemoryTokens(null, null);

    expect(getInMemoryTokens()).toEqual({
      accessToken: null,
      refreshToken: null,
    });
  });
});
