#!/usr/bin/env python3
"""
Test script for error handling in DarijaLang
"""

import sys

def test_with_file(filename, expected_exit_code=0):
    print(f"Testing error handling with file: {filename}")
    print(f"Expected exit code: {expected_exit_code}")
    
    # Import here to avoid circular imports
    import darija_c_emitter
    
    try:
        with open(filename, 'r') as f:
            source = f.read()
            
        print(f"Compiling and running: {filename}")
        exit_code = darija_c_emitter.compile_and_run(source, keep_c=True)
        print(f"Program exited with code: {exit_code}")
        return exit_code == expected_exit_code
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Use the default test files with expected exit codes
        test_files = [
            ("simple_error_test.darija", 1),  # Expected to fail with exit code 1 (uncaught exception)
            ("error_handling_test.darija", 0)  # Expected to succeed
        ]
        
        success = True
        for test_file, expected_code in test_files:
            if not test_with_file(test_file, expected_code):
                success = False
                print(f"Test failed for {test_file}")
                
        if success:
            print("All tests passed!")
        else:
            print("Some tests failed!")
            sys.exit(1)
    else:
        # Test a specific file
        test_file = sys.argv[1]
        # Use exit code 1 for simple_error_test.darija since it has an uncaught exception
        expected_code = 1 if test_file == "simple_error_test.darija" else 0
        if not test_with_file(test_file, expected_code):
            print(f"Test failed for {test_file}")
            sys.exit(1)
        
        print("Test passed!")
