/**
 * Test component to verify logger works
 */

import { logger } from "@/utils/logger";

logger.debug("🔥🔥🔥 TEST: This file is loaded! 🔥🔥🔥");

export function ConsoleTest() {
  logger.debug("🔥🔥🔥 TEST: ConsoleTest component rendering! 🔥🔥🔥");

  return (
    <div
      style={{
        position: "fixed",
        top: 10,
        right: 10,
        background: "red",
        color: "white",
        padding: "10px",
        zIndex: 9999,
        border: "3px solid yellow",
      }}
    >
      🔥 CONSOLE TEST ACTIVE 🔥
      <br />
      Check the console (F12)
    </div>
  );
}
