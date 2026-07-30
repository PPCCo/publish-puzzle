# Puzzle/Coloring Book publishing house

## Book Publishing House

I have an existing Claude AI framework/toolkit for a books publishing company in `/Users/qaiser.abbas/Dev/my-repos/bk-pub` containing agents, commands, hooks, mcp, patterns, rules, schemas, scripts, skills, standards, templates, and workflows that work together to act as a whole company with multiple agents and skills acting as experts to perform different tasks to create an automated and autonomous process of creating interesting, attractive, enterprise grade, professional and high quality picture-books and audiobooks for all ages, from kids aged 6-12 years, to teenagers and adults, including story books, encyclopedias, geography, science, biology, physics, and other sciences and concepts. The framework’s primary purpose is to:

1. generate book content;
2. review and revise it through specialist agents;
3. create illustrations and other media;
4. produce EPUB, PDF, print, audiobook, and read-along formats;
5. generate covers, descriptions, keywords, pricing suggestions, and marketplace assets;
6. prepare packages that can be uploaded to Amazon, eBay, and other marketing and sales channels.

## TASK

I want to create a similar framework for another publishing house that creates Puzzle & activity books (word search, sudoku, crossword, mazes), coloring books and specialized coloring books, Guided journals, structured workbooks, practical digital & printable planners, Digital printables & templates (Etsy specifically), and any other similar products that plays to Claude's actual strength — organizing content logically (habit trackers, prompts, reflection sections, etc) rather than blank pages.

---

### The categories

#### Puzzle & activity books (word search, sudoku, crossword, mazes)

This is a language-agnostic content, would be pretty much automated and autonomous creation of Puzzle & activity books. At $8-$12 price points, and top publishers earning $20K-$50K/month from Sudoku portfolios. The puzzle book market exceeds $450M annually on Amazon with 13% year-over-year growth driven by screen fatigue and wellness trends. Large print is the highest revenue segment, with top books earning $5,000 to $15,000 a month, and the winning formula stacks a puzzle type, a specific theme, and a target audience — e.g. "large print word search for seniors with dementia, calming themes" — rather than generic "Word Search Vol 1" titles. Claude can generate the puzzles programmatically (via code execution — actual sudoku/word-search/crossword generation algorithms, not "asking an LLM to invent a grid"), lay out answer keys, and produce cover copy — this is close to fully autonomous.

There are some MCP Servers available as well (`https://mcpmarket.com/tools/skills/sudoku-puzzle-manager-1`) but I would like a bespoke solution, maybe getting ideas from existing solutions.

#### Coloring books

There are already published Claude Code Skills doing this exact pipeline. One skill provides a 9-phase pipeline turning any topic into a coloring book business, handling market research, image sourcing, AI-powered line-art conversion, vectorization, QA, and automated listing on Etsy, ebay, Gumroad, and Amazon KDP, etc. In 2026, "bold and easy" coloring books are a specific style pulling ahead of traditional coloring books on KDP, and large-print seasonal coloring books are a consistent winner.

There are some MCP Servers for Coloring Books available (`https://mcpmarket.com/tools/skills/coloring-book-creator-publisher`) but again, I would like a bespoke solution, maybe getting ideas from existing solutions.

#### Guided journals & structured workbooks

Guided journals, specialized coloring books, puzzle books, and practical planners targeting specific demographics are among the most profitable KDP niches for 2026, and the trend gaining the most traction is large-print seasonal collections and structured journals with clear sections, not just lined pages. This plays to Claude's actual strength — organizing content logically (habit trackers, prompts, reflection sections) rather than blank pages.

#### Digital printables & templates (Etsy specifically)

The best digital products to sell on Etsy in 2026 are digital planners, printable planners, Excel budget templates, social media templates, website templates, AI/ChatGPT prompts, fonts, Lightroom presets, and ebooks, and printable planners and social media templates offer the best balance of demand and ease of creation for beginners, while website templates and ebooks have the highest average order value. Given your Next.js background, Canva/website template packs are a natural extension.

## Two important operational realities

1. **AI disclosure is now mandatory on KDP, not optional.** Every book submission now includes a required section to declare AI's role in the content. You must disclose AI-generated text, images, or translations that appear in the book, but you don't need to disclose ordinary AI-assisted workflow tasks that never become book content. The disclosure doesn't appear on your product page and doesn't block publication by itself — disclosed AI content is publishable if it meets normal quality guidelines, but undisclosed AI-generated content can lead to blocked books or account suspension, with enforcement tightening through 2025-2026. Worth building this checkbox into your pipeline as a standard step, not an afterthought.

2. **Volume without quality gets flagged.** Publishing dozens of unedited AI books rapidly is the fastest way to get flagged, and even with proper disclosure, Amazon may remove books that don't meet quality standards. This actually argues _for_ your kids' non-fiction book approach and against pure low-content spam — a Claude-driven pipeline with a genuine QA sub-agent step (like the coloring book skill's visual scoring stage) will hold up better than a batch-and-blast approach.'

## How this maps to an actual Claude-driven setup

Given that I'm comfortable with agentic tooling, the realistic architecture is: a Claude Skill (or Claude Code project) per product type — puzzle-generator skill, coloring-book skill, journal-layout skill, cover-design skill — each handling research → content generation → print-ready file assembly → marketplace listing draft, with a human QA gate before you hit publish. Skills are essentially natural-language instructions plus a toolbox that don't require coding to build, so you could realistically stand up 3-4 of these part-time.

---

## MORE INFO ON TASK

There is some research that I've done with Claude, and Claude came up with a few suggestions. They are captured in the documents inside @research/ folder.

The puzzle/coloring books Publishing House framework should be similar to `/Users/qaiser.abbas/Dev/my-repos/bk-pub`. If there are any enhancements that can be made, then make them directly in this project, and create a plan for these enhancements to be made in `/Users/qaiser.abbas/Dev/my-repos/bk-pub`. If you think it will be better to merge the requirements for this puzzle/coloring books Publishing framework (including those in @research/ folder) into the books publishing framework `/Users/qaiser.abbas/Dev/my-repos/bk-pub` then let me know about that as well.
