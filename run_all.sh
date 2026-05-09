#!/bin/bash

OUTPUT_DIR="run_outputs"
mkdir -p "$OUTPUT_DIR"

echo "Run all in input/ ..."
echo "--------------------------------------------------------"

for config_path in input/os_*; do
    if [ -f "$config_path" ]; then
        config_name=$(basename "$config_path")
        echo "-> Running: $config_name"
        ./os "$config_name" "$OUTPUT_DIR"
    fi
done

echo "--------------------------------------------------------"
echo "Completed! Outputs at: $OUTPUT_DIR/"