# Plan: Fix Blank PDF Pages — Implement Sudoku Grid Rendering in layout.py

## Context

The PDFs produced by `build_interior()` in `layout.py` contain only a two-line text stub per page
("Sudoku #1 / Difficulty: easy") because `_draw_placeholder_page()` was always a skeleton never
replaced with real rendering logic. The actual 9×9 puzzle grid data is present in the generated
batch JSON but is discarded by `_content_pages()`, which strips each item to `{type, index,
difficulty}`. The fix threads grid data through and adds a proper sudoku grid renderer.

Audience: `senior-large-print` — `body_type_pt: 18.0`, high contrast required, one puzzle per
page. Trim: 8.5×11. Enforced in `accessibility.py`: ≥16pt body, high contrast.

## File to modify

**`.claude/scripts/publishing_house/layout.py`** — the only file that needs changes.

## Implementation

### Step 1 — Thread puzzle data through `_content_pages()` (lines 93–103)

Add `payload` and `solution` to the descriptor dicts so the renderer receives the actual grid:

```python
content.append({
    "type": ctype, "index": item.get("index"), "difficulty": item.get("difficulty"),
    "payload": item.get("payload"),   # {"grid": [[...9x9...]], "given_count": N, "size": 9}
    "solution": item.get("solution"), # {"grid": [[...9x9...]]}
})
solutions.append({
    "type": ctype, "index": item.get("index"),
    "solution": item.get("solution"),
})
```

### Step 2 — Add `_draw_sudoku_page()` (insert after `_draw_placeholder_page`)

Renders a full 9×9 sudoku grid onto a canvas page. All sizes derived from trim at render time:

```python
MARGIN = 0.75  # inches
HEADER_H = 1.0  # inches — title + difficulty label
grid_area = min(width_in - 2*MARGIN, height_in - 2*MARGIN - HEADER_H)
cell_size = grid_area / 9  # ~0.78in on 8.5×11, scales to other trims
```

Layout:
- Header: puzzle number in 18pt Helvetica-Bold + difficulty in 14pt Helvetica (top-left, 0.75in margin)
- Grid: centred horizontally, placed below header
- Cell borders: 0.5pt thin lines for cell divisions; 2.0pt thick for 3×3 box divisions (drawn with `c.rect()` and `c.line()`)
- Digits: non-zero cells drawn centred in cell using 18pt Helvetica-Bold via `c.drawString()`; zero cells left blank
- Black on white — no grey fill (high contrast for senior-large-print)
- `c.showPage()` at end

Signature:
```python
def _draw_sudoku_page(c, inch, width_in, height_in, title, difficulty, grid, *, is_solution=False):
```
When `is_solution=True`: all 81 digits filled from the solution grid, title prefixed "Solution:".

### Step 3 — Update `build_interior()` loops (lines 128–140)

Replace the `_draw_placeholder_page` calls in the content and solution loops with type-dispatched
calls. The dispatching logic is simple: if `page["type"] == "sudoku"`, call `_draw_sudoku_page()`;
otherwise fall back to `_draw_placeholder_page()` (backward-compatible for other content types).

Content loop (line 129):
```python
if page.get("type") == "sudoku" and page.get("payload"):
    _draw_sudoku_page(c, inch, width_in, height_in,
        f"Sudoku #{(page['index'] or 0) + 1}", page.get("difficulty", ""), 
        page["payload"]["grid"])
else:
    _draw_placeholder_page(c, inch, width_in, height_in, ..., ...)
```

Solution loop (line 138):
```python
if page.get("type") == "sudoku" and page.get("solution"):
    _draw_sudoku_page(c, inch, width_in, height_in,
        f"Solution #{(page['index'] or 0) + 1}", "",
        page["solution"]["grid"], is_solution=True)
else:
    _draw_placeholder_page(...)
```

### Step 4 — Leave all other functions untouched

`_draw_placeholder_page`, `build_cover`, `build_proof`, `link_digital_bundle`, `_load_batches`,
`_trim` — no changes. Front matter, solutions divider, blank pad pages remain as placeholders.

## Artifact impact

The rebuilt interior PDF will have a different SHA-256. The interior approval
(`apr-interior-20260731t130811z-15865981.json`) will become stale after rebuild. The user must
be informed that downstream approvals referencing the old interior hash need re-evaluation.

## Verification

1. Regenerate interior: `python3 .claude/scripts/ph_cli.py build interior <project-id>`
2. Decode a content stream from the rebuilt PDF — must contain `re` (rect) and `Tj` (text with digits)
3. Rebuild KDP package: `python3 .claude/scripts/ph_cli.py package kdp <project-id>`
4. Rebuild Etsy package: `python3 .claude/scripts/ph_cli.py package etsy <project-id>`
5. Confirm a sample page has a proper 9×9 grid with given digits and blank cells — not just a title
