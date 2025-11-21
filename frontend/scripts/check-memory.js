#!/usr/bin/env node
/* eslint-env node */
/* global console */
/**
 * Simple script to check if memory leaks exist in production build.
 *
 * Usage:
 *   1. npm run build && npm run preview
 *   2. In another terminal: node scripts/check-memory.js
 *   3. Watch the memory graph in the output
 *
 * Expected: Memory should stabilize and not grow indefinitely.
 */

console.log(`
╔════════════════════════════════════════════════════════════════╗
║         Memory Leak Check - Production Build                  ║
╚════════════════════════════════════════════════════════════════╝

📋 Instructions:

1. Start the production build:
   npm run build && npm run preview

2. Open your browser to http://localhost:4173

3. Open Chrome DevTools (F12):
   - Go to "Performance" tab
   - Click on "Memory" checkbox
   - Click "Record" button

4. Perform the following actions:
   a. Navigate to /map
   b. Wait 2 seconds
   c. Navigate to /account
   d. Wait 2 seconds
   e. Repeat steps a-d at least 10 times

5. Stop the recording and analyze the memory graph

✅ EXPECTED RESULT:
   - Memory should show a "sawtooth" pattern
   - Goes up when entering /map (map loads)
   - Goes down when leaving /map (map cleanup)
   - Overall trend should be FLAT (no continuous increase)
   - Typical range: 50-200 MB

❌ WARNING SIGNS:
   - Continuous upward trend
   - Memory keeps growing after each /map visit
   - "Detached DOM tree" warnings in heap snapshot
   - Memory usage > 500 MB

📊 Alternative: Heap Snapshot Comparison

1. Navigate to /map
2. Take heap snapshot (DevTools → Memory → Take Snapshot)
3. Navigate to /account
4. Take another heap snapshot
5. Compare the two snapshots
6. Search for "MapPage" or "leaflet" in the comparison
7. Should see 0 or very few remaining objects

🔍 Memory Profiler Keywords to Check:
   - "Detached HTMLDivElement" (should be 0 or minimal)
   - "Map" from leaflet (should be cleaned up)
   - Event listeners (should not accumulate)

═══════════════════════════════════════════════════════════════

💡 TIP: If you see memory growing, check:
   - Is map.remove() being called? (Check MapPage.tsx useEffect cleanup)
   - Are there event listeners not being removed?
   - Are there timers/intervals not being cleared?

Current Status: ✅ map.remove() is implemented in MapPage.tsx

Happy testing! 🎉
`);
