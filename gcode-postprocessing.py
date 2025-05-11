import argparse

class GCodeSection:
    def __init__(self, label=None, layer=None, perimeter=None, debug=False):
        self.lines = []
        self.debug = debug
        self.label = label
        self.layer = layer
        self.perimeter = perimeter

    def append(self, line):
        if self.debug:
            debug_info = []
            if self.layer is not None:
                debug_info.append(f"Layer {self.layer}")
            if self.perimeter is not None:
                debug_info.append(f"Perimeter {self.perimeter}")
            if self.label:
                debug_info.append(self.label)
            line = f"{line} ; {' | '.join(debug_info)}"
        self.lines.append(line)

    def __iter__(self):
        return iter(self.lines)

class Perimeter:
    def __init__(self, layer_number, index, debug=False):
        self.move = GCodeSection("Move", layer_number, index, debug)
        self.prints = GCodeSection("Print", layer_number, index, debug)

class Layer:
    def __init__(self, number, debug=False):
        self.number = number
        self.header = GCodeSection("Header", number, None, debug)
        self.move = GCodeSection("Move", number, None, debug)
        self.perimeters = []

class GCodeParser:
    def __init__(self, debug=False):
        self.debug = debug
        self.initial = GCodeSection("Initial", debug=debug)
        self.final = GCodeSection("Final", debug=debug)
        self.layers = []



    def parse(self, lines):
        current_layer = None
        current_perimeter = None
        mode = "initial"
        g92_e0_seen = 0
        after_g92_e0 = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith(";LAYER_CHANGE"):
                if current_layer:
                    if current_perimeter:
                        current_layer.perimeters.append(current_perimeter)
                        current_perimeter = None
                    self.layers.append(current_layer)
                current_layer = Layer(len(self.layers), self.debug)
                current_layer.header.append(stripped)
                g92_e0_seen = 0
                after_g92_e0 = False
                mode = "layer"
                continue

            if mode == "initial":
                self.initial.append(stripped)
                continue

            if stripped.startswith("G92 E0"):
                after_g92_e0 = True
                if mode == "layer":
                    g92_e0_seen += 1
                    current_layer.move.append(stripped)
                    if (current_layer.number == 0 and g92_e0_seen == 2) or \
                    (current_layer.number > 0 and g92_e0_seen == 1):
                        current_perimeter = Perimeter(current_layer.number, len(current_layer.perimeters), self.debug)
                        mode = "perimeter"
                elif mode == "perimeter":
                    if current_perimeter:
                        current_layer.perimeters.append(current_perimeter)
                    current_perimeter = Perimeter(current_layer.number, len(current_layer.perimeters), self.debug)
                    current_perimeter.move.append(stripped)
                continue

            if after_g92_e0 and stripped.startswith("G1 Z"):
                current_layer.move.append(stripped)
                after_g92_e0 = False
                continue
            else:
                after_g92_e0 = False

            if mode == "layer":
                current_layer.move.append(stripped)
                continue

            if mode == "perimeter":
                if stripped.startswith(";TYPE:Custom"):
                    if current_perimeter:
                        current_layer.perimeters.append(current_perimeter)
                        current_perimeter = None
                    self.layers.append(current_layer)
                    current_layer = None
                    mode = "final"

                    self.final.append(stripped)
                    for remaining in lines[i+1:]:
                        self.final.append(remaining.strip())
                    break  
                elif current_perimeter and not current_perimeter.prints.lines and not stripped.startswith("G1 F"):
                    current_perimeter.move.append(stripped)
                elif current_perimeter:
                    current_perimeter.prints.append(stripped)

        if mode != "final" and current_layer:
            if current_perimeter:
                current_layer.perimeters.append(current_perimeter)
            self.layers.append(current_layer)

    def render(self, output_path):
        with open(output_path, "w") as out:
            for line in self.initial:
                out.write(line + "\n")
            for layer in self.layers:
                for line in layer.header:
                    out.write(line + "\n")
                for line in layer.move:
                    out.write(line + "\n")

                # Reverse perimeters only for even-numbered layers (1, 3, 5, ...)
                perimeters = (
                    list(reversed(layer.perimeters))
                    if layer.number % 2 == 1
                    else layer.perimeters
                )

                for perimeter in perimeters:
                    for line in perimeter.move:
                        out.write(line + "\n")
                    for line in perimeter.prints:
                        out.write(line + "\n")

            for line in self.final:
                out.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="Parse and rewrite G-code with optional debug comments.")
    parser.add_argument("input", help="Path to the input G-code file.")
    parser.add_argument("output", help="Path to the output G-code file.")
    parser.add_argument('--debug', action='store_true', help='Append debug comments to G-code lines.')
    args = parser.parse_args()

    gcode_parser = GCodeParser(debug=args.debug)
    with open(args.input, "r") as f:
        lines = f.readlines()
    gcode_parser.parse(lines)
    gcode_parser.render(args.output)

if __name__ == "__main__":
    main()
