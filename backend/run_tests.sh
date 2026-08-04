#!/bin/bash
# Test Scripts Runner for Unix/Linux/Mac
# Run all StockIT test scripts

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo
    echo "================================================================================"
    echo "  $1"
    echo "================================================================================"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

test_jira_raw() {
    print_header "Jira Raw API Test"
    python test_jira_raw.py
    local result=$?
    echo
    if [ $result -eq 0 ]; then
        print_success "Test completed! Check jira_raw_response.json for raw data"
    else
        print_error "Test failed! Check your Jira credentials in .env"
    fi
    echo
    read -p "Press Enter to continue..."
    return $result
}

test_jira_full() {
    print_header "Jira Service Test (Full)"
    python test_jira_connection.py
    local result=$?
    echo
    if [ $result -eq 0 ]; then
        print_success "Test completed! Check jira_tickets_export.json for parsed data"
    else
        print_error "Test failed! Check the output above for details"
    fi
    echo
    read -p "Press Enter to continue..."
    return $result
}

test_auth() {
    print_header "Authentication Flow Test"
    print_warning "Make sure the backend is running first!"
    print_info "Start it with: uvicorn app.main:app --reload"
    echo
    read -p "Press Enter to continue with test..."
    python test_auth_flow.py
    echo
    read -p "Press Enter to continue..."
}

test_all() {
    print_header "Running All Tests"
    
    echo "[1/3] Testing Jira Raw API..."
    python test_jira_raw.py
    local test1=$?
    
    echo
    echo "[2/3] Testing Jira Service..."
    python test_jira_connection.py
    local test2=$?
    
    echo
    echo "[3/3] Testing Authentication (make sure backend is running)..."
    python test_auth_flow.py
    local test3=$?
    
    print_header "Test Results Summary"
    
    if [ $test1 -eq 0 ]; then
        print_success "Jira Raw API Test: PASSED"
    else
        print_error "Jira Raw API Test: FAILED"
    fi
    
    if [ $test2 -eq 0 ]; then
        print_success "Jira Service Test: PASSED"
    else
        print_error "Jira Service Test: FAILED"
    fi
    
    if [ $test3 -eq 0 ]; then
        print_success "Auth Flow Test: PASSED"
    else
        print_error "Auth Flow Test: FAILED"
    fi
    
    echo
    read -p "Press Enter to continue..."
}

start_server() {
    print_header "Starting Backend Server"
    print_info "Server will start with hot reload enabled"
    print_info "Press Ctrl+C to stop the server"
    echo
    read -p "Press Enter to start..."
    python -m uvicorn app.main:app --reload
}

show_menu() {
    clear
    print_header "StockIT Test Suite"
    echo "Please select a test to run:"
    echo
    echo "  1. Test Jira Connection (Quick - Raw API)"
    echo "  2. Test Jira Service (Full - With Statistics)"
    echo "  3. Test Authentication Flow"
    echo "  4. Run All Tests"
    echo "  5. Start Backend Server"
    echo "  6. Exit"
    echo
}

main() {
    while true; do
        show_menu
        read -p "Enter your choice (1-6): " choice
        
        case $choice in
            1)
                test_jira_raw
                ;;
            2)
                test_jira_full
                ;;
            3)
                test_auth
                ;;
            4)
                test_all
                ;;
            5)
                start_server
                ;;
            6)
                echo
                echo "Goodbye!"
                exit 0
                ;;
            *)
                echo
                print_error "Invalid choice. Please try again."
                sleep 2
                ;;
        esac
    done
}

# Make script executable
chmod +x "$0" 2>/dev/null

# Run main menu
main
