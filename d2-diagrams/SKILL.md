---
name: d2-diagrams
description: D2 diagram language reference - layout engines, styling, composition, and pitfalls. Use when writing, debugging, or explaining D2 diagrams.
paths: "**/*.d2"
---

# D2 Diagram Language Reference

## Layout Engines

### ELK (recommended)
- Set in file: `vars: { d2-config: { layout-engine: elk } }`
- Only engine that respects `width`/`height` on containers
- Per-container `direction` is silently ignored - only global direction works
- Slower than dagre but produces better layouts for complex graphs
- CLI spacing flags (cannot be set in d2-config):
  - `--elk-nodeNodeBetweenLayers` (default 70) - spacing between layers
  - `--elk-edgeNodeBetweenLayers` (default 40) - edge-to-node spacing
  - `--elk-padding` (default `[top=50,left=50,bottom=50,right=50]`) - container padding
  - `--elk-nodeSelfLoop` (default 50)
- `--elk-algorithm=orthogonal` crashes on complex diagrams - avoid it

### Dagre (default)
- Per-container `direction` does NOT work (silently ignored, no error)
- Known bug: nested nodes can overflow parent container boundaries
- Faster than ELK

### TALA (not recommended, proprietary, separate install)
- Only engine that supports per-container `direction` and `near: OtherObject`
- Can crash (signal: killed) on complex diagrams with many edges
- Install: `curl -fsSL https://d2lang.com/install-tala.sh | sh -s --`

## What Does NOT Affect Layout (verified)
- Node and connection definition order in the file have zero effect on ELK layout - don't waste time reordering.

## What DOES Affect Layout
- **Container hierarchy**: the most reliable grouping mechanism.
- **Global `direction`**: `down`, `right`, `left`, `up`.
- **`width`/`height` on containers** (ELK only): constrains container size.
- **Grid layout** (`grid-rows`/`grid-columns`): forces structured placement but bypasses routing.

Layout is minimally configurable; aim for correctness rather than manual positioning.

## `near` Keyword - Critical Pitfall
- Shapes with `near` (e.g. `near: top-center`) are REMOVED from the layout graph before the engine runs, so you cannot connect objects inside a `near`-positioned container to objects outside it — attempts cause broken or scattered layouts.
- Use `near` ONLY for detached elements: titles, legends, annotations.
- Valid constants: `top-left`, `top-center`, `top-right`, `center-left`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`.
- `near: OtherObject` only works with TALA.

## Grid Layout
- `grid-columns` and `grid-rows` bypass the layout engine entirely
- Cross-grid connections render as simple straight lines, not routed elbow paths
- Don't use grid on containers that need routed connections between children and external nodes
- Grid is good for legends, packaging lists, or any container where internal routing doesn't matter

## Invisible/Hidden Elements
- Disconnected nodes may not render visibly in dagre or ELK - always give nodes at least one connection
- `style.opacity: 0` on connections works as layout hints in both engines
- To fully hide a container (for layout grouping only):
  ```d2
  MyGroup: MyGroup {
      style.fill: transparent
      style.stroke: transparent
      style.font-color: transparent
  }
  ```
- Or define a `group` class for reuse

## `_.` References
- `_.Foo` inside a container references the parent-scoped `Foo` node
- It does NOT move the node into the container for layout purposes
- Don't use `_.` for layout grouping

## Width/Height
- Cannot set on root diagram level - only shapes and containers
- Works on individual shapes in all engines
- Works on containers only in ELK
- `person` shapes get deformed in grid layouts - set explicit `width`/`height` to preserve aspect ratio

## Font Size
- Setting `style.font-size` uniformly on all classes has no visible effect - D2 scales the entire diagram to fit the viewport
- To make text appear larger relative to boxes, reduce `pad` to give more canvas space

## Composition / File Splitting
- `...@./file.d2` (spread import) merges the file's contents into the current scope
- Imported nodes are fully referenceable for connections (e.g., `Battery.BMS`)
- A file can import another and add more nodes/connections on top (layered composition)
- To nest an imported node inside a container, prefix the node name in the imported file:
  ```d2
  # In battery.d2
  Peripherals.Battery: Battery { ... }
  ```
- Classes must be imported separately - they don't carry over from child imports

## Styling
- Classes are defined in a `classes: {}` block and applied with `{class: myclass}`
- Classes can style both nodes and connections
- Key style properties for nodes: `style.fill`, `style.stroke`, `style.stroke-dash`, `style.font-size`, `style.bold`, `style.border-radius`, `shape`
- Key style properties for connections: `style.stroke`, `style.stroke-width`, `style.stroke-dash`
- Available shapes: `rectangle`, `circle`, `oval`, `cloud`, `person`, `text`, `diamond`, `hexagon`, `cylinder`, `queue`, `parallelogram`
- `border-radius` on connections controls corner roundness (only applies to engines with elbow routing like ELK)

## D2 Config Vars

Always at the top of the file:

```d2
vars: {
    d2-config: {
        layout-engine: elk    # elk, dagre, or tala
        pad: 10               # margin around rendered diagram (px)
    }
}
```

ELK spacing flags are CLI-only and cannot be set in d2-config.

## Common Patterns

### Semantic grouping (invisible container)
```d2
classes: {
    group: {
        style.fill: transparent
        style.stroke: "#9CA3AF"
        style.stroke-dash: 3
        style.font-color: "#9CA3AF"
    }
}
MyGroup: My Group {class: group}
```

### Legend with connection examples
```d2
legend: Legend {
    near: bottom-center
    connections: Connections {
        style.fill: transparent
        style.stroke: transparent
        p1.style.opacity: 0
        p2.style.opacity: 0
        p1 -> p2: Power {class: power}
    }
}
```

### Rendering commands
```bash
# Live preview
d2 --watch src/file.d2 src/file.svg

# Render to PNG
d2 src/file.d2 src/file.png
```
