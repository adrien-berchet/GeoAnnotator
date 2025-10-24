#!/bin/bash
# Run integration tests for GeoAnnotator
# Usage: ./run_integration_tests.sh [scenario_name]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}GeoAnnotator Integration Tests Runner${NC}"
echo "========================================"

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: Must run from backend/ directory${NC}"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo -e "${RED}Error: PostgreSQL is not running${NC}"
    exit 1
fi

# Check if test database exists
if ! psql -lqt | cut -d \| -f 1 | grep -qw geoannotator_test; then
    echo -e "${YELLOW}Creating test database...${NC}"
    createdb geoannotator_test
    psql geoannotator_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"
fi

# Run migrations
echo -e "${YELLOW}Running migrations...${NC}"
python manage.py migrate --settings=config.settings.development --run-syncdb

# Determine which tests to run
if [ -z "$1" ]; then
    # Run all integration tests
    echo -e "${GREEN}Running all integration tests...${NC}"
    pytest tests/integration/ -v --tb=short
else
    # Run specific scenario
    case "$1" in
        auth|1)
            echo -e "${GREEN}Running Scenario 1: Authentication tests...${NC}"
            pytest tests/integration/test_scenario_auth.py -v
            ;;
        points|2)
            echo -e "${GREEN}Running Scenario 2: Points tests...${NC}"
            pytest tests/integration/test_scenario_points.py -v
            ;;
        annotations|3)
            echo -e "${GREEN}Running Scenario 3: Annotations tests...${NC}"
            pytest tests/integration/test_scenario_annotations.py -v
            ;;
        sharing|4)
            echo -e "${GREEN}Running Scenario 4: Sharing tests...${NC}"
            pytest tests/integration/test_scenario_sharing.py -v
            ;;
        import-export|export|5)
            echo -e "${GREEN}Running Scenario 5: Import/Export tests...${NC}"
            pytest tests/integration/test_scenario_import_export.py -v
            ;;
        trash|6)
            echo -e "${GREEN}Running Scenario 6: Trash tests...${NC}"
            pytest tests/integration/test_scenario_trash.py -v
            ;;
        public|7)
            echo -e "${GREEN}Running Scenario 7: Public browsing tests...${NC}"
            pytest tests/integration/test_scenario_public.py -v
            ;;
        locks|8)
            echo -e "${GREEN}Running Scenario 8: Locks tests...${NC}"
            pytest tests/integration/test_scenario_locks.py -v
            ;;
        *)
            echo -e "${RED}Unknown scenario: $1${NC}"
            echo "Available scenarios:"
            echo "  auth (1) - Authentication"
            echo "  points (2) - GPS Points"
            echo "  annotations (3) - Annotations"
            echo "  sharing (4) - Sharing"
            echo "  import-export (5) - Import/Export"
            echo "  trash (6) - Trash"
            echo "  public (7) - Public browsing"
            echo "  locks (8) - Editing locks"
            exit 1
            ;;
    esac
fi

echo -e "${GREEN}Tests completed!${NC}"
