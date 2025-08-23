#!/bin/bash
echo "==> Debug: Starting WealthPath AI Backend..."
echo "==> Debug: Current directory: $(pwd)"
echo "==> Debug: Files in current directory:"
ls -la
echo "==> Debug: Contents of build.sh:"
cat build.sh
echo "==> Debug: Executing build.sh..."
bash ./build.sh