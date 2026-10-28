---
inclusion: manual
---

# ASL JSON → Draw.io High-Level Diagram Converter

## Purpose

Convert an AWS Step Functions ASL JSON definition into a **high-level** SVG diagram.
The goal is a readable overview — not a 1:1 state map. Reason about the logical intent
of groups of states and represent them as a single labelled box.

All ASL templates for this project live in `app/step-functions-templates/`.

---

## Step 1 — Read and Understand the ASL

Before drawing anything, read the full ASL JSON and mentally group states into logical phases. Ask:

- What is this cluster of states _trying to achieve_ at a business level?
- Can several states collapse into one summary box? (They almost always can.)
- Are there Parallel branches? Treat them as a single logical step — the reader cares about _what_
  is resolved, not _how many branches_ do it.

---

## Step 2 — Identify Logical Groups

Use these heuristics to collapse states:

| Pattern                                                                                             | Collapsed label                                                     |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `Pass` that sets defaults + `Choice` that checks if a value is already set + `Task` to fetch if not | "Resolve \<field\>"                                                 |
| `Parallel` with N branches each doing "use provided X or fetch default"                             | Single box: "Resolve \<thing\>"                                     |
| `Choice` + `Task` (lambda) + `Next` where condition is "already populated, skip"                    | "Populate \<field\> if missing"                                     |
| `Map` iterating over a list to call a lambda                                                        | "Resolve \<item\> for each entry"                                   |
| `Task` with `waitForTaskToken`                                                                      | "Wait for \<event description\>"                                    |
| `Choice` comparing before/after state                                                               | "Skip if already complete"                                          |
| `Task` (SSM `getParameter`)                                                                         | Absorb into the parent logical step — do not show as a separate box |
| `Succeed` / `Fail` terminals                                                                        | "Success" / "Failure" terminal nodes                                |

---

## Step 3 — Draw the High-Level Flow

There are **four** node types. Do not add others.

### Node Types

| Type         | Shape          | Fill                                       | Stroke                                                                                 | When to use                                                                                                                          |
| ------------ | -------------- | ------------------------------------------ | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Start**    | Labelled oval  | white fill, `#1a1a1a` border               | Entry point only — white ellipse with dark stroke and "Start" label, `rx="28" ry="18"` |
| **Step**     | Rounded rect   | `#dae8fc`                                  | `#6c8ebf`                                                                              | Every logical phase — whether it maps to a single Task, a Parallel group, or a Map. No distinction between "process" and "parallel". |
| **Decision** | Diamond        | `#fff2cc`                                  | `#d6b656`                                                                              | A branch the _reader_ needs to understand (skip/continue, somatic/germline, etc.)                                                    |
| **Wait**     | Rounded rect   | `#f8cecc`                                  | `#b85450`                                                                              | `waitForTaskToken` only — execution pauses for an external event                                                                     |
| **Terminal** | Stadium (pill) | `#d5e8d4` (success) or `#f8cecc` (failure) | `#82b366` / `#b85450`                                                                  | End states                                                                                                                           |

### Edge Types

| Type                       | Style                                     | When                                 |
| -------------------------- | ----------------------------------------- | ------------------------------------ |
| Normal flow                | Solid, grey `#555555`                     | Default transition                   |
| Conditional (taken path)   | Solid + short label summarising condition | Named branch from a Decision         |
| Conditional (skip/default) | Dashed, grey                              | "No change" / "already valid" bypass |
| Wait transition            | Dashed, red `#b85450`                     | Into or out of a Wait node           |

---

## Step 4 — Typography

- Font: `font-family="'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif"`
- Primary label (step name): `font-size="13"`, `font-weight="500"`, `fill="#1a1a1a"`
- Secondary label (clarifying detail): `font-size="11"`, `font-weight="400"`, `fill="#555555"`, italic
- Edge labels: `font-size="11"`, `fill="#666666"`
- Decision node text: `font-size="12"`, centred, two `<tspan>` lines if needed
- Do **not** apply the sketch filter to text elements

---

## Step 5 — Layout Rules

Target a diagram that is roughly **square or landscape** (width ≥ height), not a tall narrow strip.
GitHub renders images at full container width, so a square or wide diagram makes much better use of
the available space than a single vertical column.

### Two-column snake layout

Split the flow across two columns. Each column flows strictly top-to-bottom. Column-to-column
handoff uses a routing channel _below_ all nodes in both columns:

- **Column A** (cx ≈ 20%): Start + first half of logical steps
- **Column B** (cx ≈ 80%): second half of logical steps + final terminal

**Handoff connector** (Col A → Col B):

- Depart from the _bottom_ of the last Col A node
- Drop to a routing channel y-value that is safely _below_ the lowest node bottom in both columns (add 60 px margin)
- Sweep right to Col B centre x, offset ±25 px from cx to avoid sharing verticals with internal Col B edges
- Rise to the _top_ of the first Col B node (y = box top + 1 px)

**Arrow tip placement** — always target 1 px inside the receiving box edge (not the box centre).
This prevents the arrowhead from landing inside the box body.

**No backwards arrows** — if a connector would need to go upward on the same column, reroute
it as a side float (see below) or move it to the handoff channel.

### Side float nodes

For short-circuit exits (e.g. "Already valid → Success") and intermediate events that feed back
into the main flow (e.g. "Put DRAFT update (intermediate)"):

- Float the node to the _right_ of its triggering node, connected by a short horizontal arrow
- The float node should not block any vertical routing channels
- If the float feeds back into the main flow, route its output _down_ to a horizontal routing
  line above the target node, then left/right into the target

### No-overlap rule

Before finalising any edge, verify it does not share a line segment with any other edge or
pass through any node box. Use distinct x or y offsets to separate parallel routes:

- Left-side bypass: x = col_cx − 30 (e.g. the "No change" dashed path)
- **Handoff between columns: route through the gap between columns** (the clear corridor between
  Col A right edge and Col B left edge). Never route a handoff up or down the far edge of a column —
  that path passes through every node in that column.
- Handoff path: `Col A right edge → right to gap centre x → up/down to target row y → right to Col B left edge`
- Bottom routing channel (y below all nodes): only use this if the gap corridor is not available

### Terminal side-branch rule

If a decision branch leads to a side-float node (e.g. "Put DRAFT update intermediate") that
represents an _end_ of that execution path, **do not draw an arrow out of it**. The branch
terminates there. The other branch (the skip/default path) continues the main flow independently.
These two branches are mutually exclusive — showing a merge back into the main flow is incorrect.

### Node sizing

- Step box: `width="300" height="62"`
- Decision diamond: span ±120 px horizontally, ±31 px vertically from centre
- Start circle: `r="18"`
- Terminal pill: `width="200" height="46"` with `rx="23"`

### Spacing

- Vertical gap between node tops within a column: 110 px
- Horizontal gap between column centres: ≈ 550 px
- Canvas padding: 25 px sides, 30 px top, 50 px bottom (room for legend)
- Target canvas ratio: landscape or square (width ≥ height)

### Labels

Sentence-case, ≤ 10 words on the primary line. Secondary italic line for clarifying detail.
No ARNs, no JSONata expressions.

---

## Step 6 — Write the draw.io XML (`.drawio`)

Produce a `.drawio` file with a valid `<mxfile>` wrapper. This is the editable source of truth.
The SVG is always generated from this file using the drawio CLI (see Step 8).

### mxCell conventions

Every node is an `<mxCell vertex="1">` and every edge is an `<mxCell edge="1">`.

**Always set explicit connection point pins on every edge** using `exitX/exitY/exitDx/exitDy`
and `entryX/entryY/entryDx/entryDy`. This ensures arrowheads land exactly on box edges rather
than floating near the centre:

```
exitX=0.5;exitY=1;exitDx=0;exitDy=0;   ← depart bottom-centre of source
entryX=0.5;entryY=0;entryDx=0;entryDy=0;  ← arrive top-centre of target
exitX=1;exitY=0.5;...  ← depart right-centre (for horizontal connections)
entryX=0;entryY=0.5;...  ← arrive left-centre
```

**Never omit connection pins** — without them draw.io picks an arbitrary attach point and
arrowheads will not settle cleanly onto the receiving node.

### Node sizing

- Standard Step box: `width="300" height="62"` — increase height to `90` or more if the label
  wraps to three lines
- Side-float nodes that need vertical space to avoid arrow overlap with adjacent nodes:
  size them taller (e.g. `height="136"`) and position `y` so their vertical centre aligns
  with the connecting edge's `entryY=0.5`
- Decision diamond: `width="240" height="62"`
- Start oval: `width="56" height="36"`
- Terminal pill (Success/Failure ellipse): `width="200" height="46"`

### Vertical gap between nodes

Use **110 px** between the top edges of consecutive nodes in the same column (i.e. if node A
top is `y=118`, node B top is `y=228`). This gives enough whitespace for edge labels and
arrowheads without cramping.

### Waypoint routing for cross-column edges

When an edge routes through the gap between columns, provide explicit `<Array as="points">`
waypoints. The key rule is:

**The final waypoint before the target must share the same `x` (for horizontal entry) or
same `y` (for vertical entry) as the entry point on the node.** This guarantees the last
segment of the edge is a perfectly straight line so the arrowhead sits cleanly.

The edge may still enter a node from any side — what matters is that the _final approach_
segment is straight, not diagonal.

Example: edge exits bottom-centre of source (`exitX=0.5;exitY=1`) and enters left-centre of
target (`entryX=0;entryY=0.5`, entry point `x=575, y=149`). The last waypoint must be at the
same `y=149` so the final segment is a straight horizontal line:

```xml
<mxCell id="e8" ...
  exitX=0.5;exitY=1;exitDx=0;exitDy=0;
  entryX=0;entryY=0.5;entryDx=0;entryDy=0; ...>
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="175" y="640"/>  <!-- straight down from source bottom-centre -->
      <mxPoint x="553" y="640"/>  <!-- sweep across the inter-column corridor   -->
      <mxPoint x="553" y="149"/>  <!-- rise to same y as entry point            -->
      <!-- final segment: x=553 → x=575 at y=149, perfectly horizontal         -->
    </Array>
  </mxGeometry>
</mxCell>
```

The same principle applies for vertical entry (`entryX=0.5;entryY=0`): the last waypoint must
share the same `x` as the entry point so the final segment is straight vertical.

**Never use `exitX=1;exitY=0.5` (right-centre exit) with downward waypoints** — this creates
a diagonal between the exit point and the first waypoint. Always align the first waypoint's
`x` with the exit point's `x` (for horizontal exits) or `y` with the exit point's `y`
(for vertical exits).

### Edge styles

```
Normal flow:    edgeStyle=orthogonalEdgeStyle;strokeColor=#555555;strokeWidth=2;
Dashed bypass:  edgeStyle=orthogonalEdgeStyle;strokeColor=#888888;strokeWidth=2;dashed=1;dashPattern=8 4;
Wait edge:      edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;strokeWidth=2;dashed=1;dashPattern=8 4;
```

Edge label style (add to the style string): `fontSize=10;fontColor=#888888;fontStyle=2;`

---

## Step 7 — Export SVG from the draw.io CLI

After writing the `.drawio` file, export to SVG using:

```sh
xvfb-run --auto-servernum /snap/bin/drawio \
  --export --format svg \
  --output docs/draw-io-exports/<name>.svg \
  docs/draw-io-exports/<name>.drawio
```

The GPU/GL warnings in the output are harmless — the export succeeds as long as the last line
shows the `source -> dest` path. Both files are kept: the `.drawio` for editing, the `.svg`
for GitHub/browser rendering.

---

## Blueprint — populate_draft_data_sfn_template.asl.json

The diagram below is the reference blueprint produced from this workflow. Use it as a structural
template when generating diagrams for other ASL files — match the node styles, edge pin conventions,
waypoint patterns, and column layout shown here.

#[[file:../../docs/draw-io-exports/populate-draft-data.drawio]]

The logical flow this represents:

```
Start
  │
  ▼
[Validate draft data]  ──(already valid, dashed)──▶  Success
  │ (not yet valid)
  ▼
[Resolve engine parameters]      ← projectId, pipelineId, outputUri, logsUri
  │
  ▼
[Resolve library tags]           ← fastqRgidList, tumorFastqRgidList, metadata
  │
  ▼
◇ Tags or engine params changed?
  │ no change (dashed)            │ changed → [Put DRAFT update event] (branch ends)
  ▼
[Resolve readsets]               ← normal + tumor library readsets
  │
  ▼
[Resolve inputs]                 ← normal + tumor sequence data + default params
  │ (red dashed — waitForTaskToken)
  ▼
[Wait for FASTQs]                ← normal + tumor
  │
  ▼
[Add reference data]             ← germline, somatic, ORA
  │
  ▼
[Add QC tags]                    ← coverage, dup-frac, NTSM internal, NTSM external
  │
  ▼
[Add downsampling]               ← somatic only, if applicable
  │
  ▼
[Put DRAFT update event]         ← fully populated payload
  │
  ▼
Success
```

---

## Output Location

Write both files to `docs/draw-io-exports/`:

- `docs/draw-io-exports/<workflow-name>.drawio` — editable draw.io source
- `docs/draw-io-exports/<workflow-name>.svg` — generated by the CLI, used in GitHub/README

For example:

- `docs/draw-io-exports/populate-draft-data.drawio`
- `docs/draw-io-exports/populate-draft-data.svg`

---

## What NOT to do

- Do not create one box per ASL state — that defeats the purpose
- Do not distinguish between "process" boxes and "parallel group" boxes — use a single Step style
- Do not include JSONata expressions, ARNs, or SSM parameter paths in labels
- Do not use AWS Step Functions console colours (orange/green)
- Do not include Retry logic as visible nodes — it is an implementation detail

---

## Step 8 — Update the README

After generating the `.drawio` and `.svg` files, add or update an image reference in `README.md`
for each state machine diagram. Use the relative path from the repo root:

```markdown
![Diagram title](docs/draw-io-exports/<workflow-name>.svg)
```

Place the image reference directly below the heading for the corresponding pipeline state flow
section. This ensures diagrams are always visible on GitHub without needing to open separate files.
