# G-Code Post-Processing Script for Continuous 3D Concrete Printing

## Overview

This Python script is a G-code post-processor designed for **continuous 3D concrete printing**, where the extruder (e.g., a concrete pump) **cannot stop during the print**. The script modifies the perimeter printing order to optimize deposition patterns and prevent unwanted material spreading during non-retracting nozzle movements.


### Purpose

In continuous **3D concrete printing**, where the material flow cannot be stopped or retracted, it's essential to manage the **position of the nozzle between layers** to avoid unnecessary travel moves while extruding.

By default, slicers generate G-code that prints **perimeters from the inside out** on every layer. This means that:

* After finishing one layer, the nozzle ends **outside the part**.
* On the next layer, it typically starts **inside**, forcing a **travel move across the fresh concrete** while still extruding — which can cause defects or smearing.

This script corrects that by:

* **Reversing the perimeter print order** on **every second layer** (1, 3, 5, …), so they are printed **from the outside in**.
* This ensures that the nozzle **starts each layer where it ended the previous one** — outside — and follows a more natural and continuous path layer after layer.

This approach **avoids unwanted extruding moves across wet concrete**, reduces defects, and ensures a smoother, more reliable print in systems with **non-stop concrete pumps**.



## Features

- Reorders perimeters **outside-in** for even layers (1, 3, 5, ...).
- Preserves original perimeter order for odd layers (0, 2, 4, ...).
- Optional debug mode to annotate G-code lines with layer and perimeter information.

## Usage

### Command-Line Interface

```bash
python gcode_concrete_post.py input.gcode output.gcode [--debug]

