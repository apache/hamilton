// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

// Tests for verify, run with `node --test scripts/verify.test.mts` (Node 22.18 or newer, no
// dependencies). Each test builds a project of its own in a temporary directory, copies the
// launcher and verify.mts into it, writes the recipes and settings it needs, and runs the tool
// there as a contributor would. The tool's own seams stand in for the clock (VERIFY_STAMP), the
// measured duration (VERIFY_DURATION), the machine (VERIFY_MACHINE) and the run identity (--run),
// so what a run records can be compared exactly.

import { strict as assert } from "node:assert";
import { spawnSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test, type TestContext } from "node:test";

const HERE = import.meta.dirname;

const LICENSE = `<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->
`;

// grace: 0, so the watchdog of each run stops what it left at once and nothing outlives a test.
const SETTINGS = `${LICENSE}
---
ask-first: ask
grace: 0
---
- Settings of a test project.
`;

const STAMP = "20260101T120000Z";

interface Result {
  code: number | null;
  stdout: string;
  stderr: string;
}

/** The environment a fixture runs in: none of the caller's VERIFY_* or GIT_* settings, and no git config. */
function cleanEnv(extra: Record<string, string> = {}): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (!key.startsWith("VERIFY_") && !key.startsWith("GIT_")) env[key] = value;
  }
  return {
    ...env,
    GIT_CONFIG_GLOBAL: "/dev/null",
    GIT_CONFIG_NOSYSTEM: "1",
    // A fixture outside git stays outside it even when the temporary directory sits in a repository.
    GIT_CEILING_DIRECTORIES: tmpdir(),
    GIT_AUTHOR_NAME: "Test",
    GIT_AUTHOR_EMAIL: "test@example.com",
    GIT_COMMITTER_NAME: "Test",
    GIT_COMMITTER_EMAIL: "test@example.com",
    ...extra,
  };
}

/**
 * A project with the tool, its settings and the given files, removed when the test ends. The
 * returned path reaches the project through a symbolic link, as every temporary directory is
 * reached on macOS (`/var/folders` is `/private/var/folders`), so the tests hold where the path a
 * contributor works from is not the canonical one. The tool runs from the canonical path.
 */
function fixture(t: TestContext, files: Record<string, string>, settings = SETTINGS): string {
  const real = mkdtempSync(join(tmpdir(), "verify-test-"));
  const root = `${real}-link`;
  symlinkSync(real, root);
  t.after(() => {
    rmSync(root, { force: true });
    rmSync(real, { recursive: true, force: true });
  });
  mkdirSync(join(root, "scripts"));
  copyFileSync(join(HERE, "verify"), join(root, "scripts", "verify"));
  copyFileSync(join(HERE, "verify.mts"), join(root, "scripts", "verify.mts"));
  mkdirSync(join(root, "verification", "recipes"), { recursive: true });
  writeFileSync(join(root, "verification", "harness.md"), settings);
  for (const [path, text] of Object.entries(files)) write(root, path, text);
  return root;
}

function write(root: string, path: string, text: string): void {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), text);
}

/** A recipe file: the license comment, front matter, a title and the given scenarios. */
function recipe(frontMatter: string, scenarios: string): string {
  return `${LICENSE}\n---\n${frontMatter.trim()}\n---\n# A recipe\n\nWhat it checks.\n\n## Scenarios\n\n${scenarios.trim()}\n\n## Gotchas\n\n- None.\n`;
}

/** Run the tool through its launcher in the project, as a contributor would. */
function verify(root: string, args: string[], extra: Record<string, string> = {}): Result {
  const done = spawnSync("sh", [join(root, "scripts", "verify"), ...args], { cwd: root, env: cleanEnv(extra), encoding: "utf8" });
  if (done.error) throw done.error;
  return { code: done.status, stdout: done.stdout, stderr: done.stderr };
}

function git(root: string, ...args: string[]): string {
  const done = spawnSync("git", ["-C", root, "-c", "commit.gpgsign=false", ...args], { env: cleanEnv(), encoding: "utf8" });
  assert.equal(done.status, 0, `git ${args.join(" ")} failed: ${done.stderr}`);
  return done.stdout.trim();
}

function commitAll(root: string, message: string): string {
  git(root, "add", "-A");
  git(root, "commit", "--quiet", "-m", message);
  return git(root, "rev-parse", "HEAD");
}

// --- check ------------------------------------------------------------------------------

test("check passes a well-formed recipe whose front matter follows the license comment", (t) => {
  const root = fixture(t, {
    "src/app.py": "",
    "tools/run.sh": "",
    "verification/recipes/app.md": recipe(
      "kind: feature\ncovers: src",
      "### tests\nRun: `sh tools/run.sh`\nProves: the app works.\n\n### judged\nRun: `true`\nProves: a person reads it.\nCheck: read",
    ),
  });
  const result = verify(root, ["check"]);
  assert.deepEqual(result, { code: 0, stdout: "check: ok\n", stderr: "" });
  assert.deepEqual(verify(root, ["list"]), { code: 0, stdout: "app  feature\n", stderr: "" });
});

test("check fails a scenario with no Run line and names the recipe and scenario", (t) => {
  const root = fixture(t, {
    "src/app.py": "",
    "verification/recipes/bad.md": recipe("kind: feature\ncovers: src", "### tests\nProves: something."),
  });
  const result = verify(root, ["check"]);
  assert.deepEqual(result, {
    code: 1,
    stdout: "bad.md: scenario 'tests' has no Run: `command` line\ncheck: 1 problem(s)\n",
    stderr: "",
  });
});

test("check fails front matter with no closing fence", (t) => {
  const root = fixture(t, {
    "verification/recipes/bad.md": `${LICENSE}\n---\nkind: feature\n# A recipe\n`,
  });
  const result = verify(root, ["check"]);
  assert.equal(result.code, 1);
  assert.equal(result.stderr, "");
  const lines = result.stdout.split("\n");
  assert.match(lines[0] ?? "", /^bad\.md: front matter has no closing `---`$/);
  assert.equal(lines.slice(1).join("\n"), "check: 1 problem(s)\n");
});

test("check fails a front matter line that is not key: value", (t) => {
  const root = fixture(t, {
    "verification/recipes/bad.md": recipe("kind: feature\nnot a field", "### tests\nRun: `true`\nProves: x."),
  });
  const result = verify(root, ["check"]);
  assert.equal(result.code, 1);
  const lines = result.stdout.split("\n");
  assert.match(lines[0] ?? "", /^bad\.md: front matter line is not `key: value`: "not a field"$/);
  assert.equal(lines.slice(1).join("\n"), "check: 1 problem(s)\n");
});

test("check names every problem: no kind, a missing cover, a missing path a scenario names, a bad Check", (t) => {
  const root = fixture(t, {
    "tools/run.sh": "",
    "verification/recipes/a-nokind.md": recipe("covers: tools", "### tests\nRun: `true`\nProves: x."),
    "verification/recipes/b-gone.md": recipe(
      "kind: feature\ncovers: src/gone.py",
      "### tests\nRun: `sh tools/missing.sh`\nProves: x.",
    ),
    "verification/recipes/c-check.md": recipe("kind: feature", "### tests\nRun: `true`\nProves: x.\nCheck: maybe"),
  });
  const result = verify(root, ["check"]);
  assert.deepEqual(result, {
    code: 1,
    stdout: [
      "a-nokind.md: front matter has no `kind:`",
      "b-gone.md: covers src/gone.py, which does not exist",
      "b-gone.md: scenario tests names tools/missing.sh, which does not exist",
      "c-check.md: scenario 'tests' Check: must be `read` or `exit`",
      "check: 4 problem(s)",
      "",
    ].join("\n"),
    stderr: "",
  });
});

test("check fails settings it cannot read", (t) => {
  const root = fixture(t, {}, `${LICENSE}\n---\nask-first: sometimes\n---\n`);
  const result = verify(root, ["check"]);
  assert.deepEqual(result, {
    code: 1,
    stdout: "verification/harness.md: ask-first must be `ask` or `run`, not 'sometimes'\ncheck: 1 problem(s)\n",
    stderr: "",
  });
});

test("a recipe key the harness does not read fails check and stops a drive, so a misspelled ask-first cannot skip the agreement", (t) => {
  const root = fixture(t, {
    "verification/recipes/costly.md": recipe("kind: feature\nask_first: it spends quota", "### go\nRun: `echo spent`\nProves: x."),
  });
  const named = "costly.md: front matter has `ask_first:`, which the harness does not read; it reads kind, covers, ask-first, dry-run";
  assert.deepEqual(verify(root, ["check"]), { code: 1, stdout: `${named}\ncheck: 1 problem(s)\n`, stderr: "" });
  const drive = verify(root, ["drive", "costly"]);
  assert.notEqual(drive.code, 0);
  assert.doesNotMatch(drive.stdout, /spent/);
  assert.match(drive.stderr, new RegExp(named.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
});

test("a settings key the harness does not read fails check", (t) => {
  const root = fixture(t, {}, `${LICENSE}\n---\nask-first: ask\naskfirst: run\n---\n`);
  assert.deepEqual(verify(root, ["check"]), {
    code: 1,
    stdout: "verification/harness.md: front matter has `askfirst:`, which the harness does not read; it reads ask-first, grace, doctor, start, running, logs, reset, stop\ncheck: 1 problem(s)\n",
    stderr: "",
  });
});

test("check accepts a scenario with no Proves line, and a drive records it as not stated", (t) => {
  // --help asks every scenario for a Proves line, but nothing enforces it: upstream deliberately
  // falls back to "(not stated)" when a scenario has none.
  const root = fixture(t, {
    "verification/recipes/loose.md": recipe("kind: feature", "### tests\nRun: `true`"),
  });
  assert.deepEqual(verify(root, ["check"]), { code: 0, stdout: "check: ok\n", stderr: "" });
  const drive = verify(root, ["drive", "loose", "--run", "test-run"], { VERIFY_STAMP: STAMP, VERIFY_DURATION: "0" });
  assert.equal(drive.code, 0);
  const evidence = read(root, `verification/evidence/loose/${STAMP}.md`);
  assert.match(evidence, /^- \*\*Proves:\*\* \(not stated\)$/m);
});

// --- affected ---------------------------------------------------------------------------

const AFFECTED_RECIPES = {
  "verification/recipes/area.md": recipe("kind: feature\ncovers: src", "### tests\nRun: `true`\nProves: src works."),
  "verification/recipes/everything.md": recipe("kind: suite\ncovers: .", "### all\nRun: `true`\nProves: all of it."),
};

test("affected names the recipe covering a changed path, lists uncovered paths, and skips evidence", (t) => {
  const root = fixture(t, { ...AFFECTED_RECIPES, "src/app.py": "one\n", "docs/guide.md": "one\n" });
  git(root, "init", "--quiet", "-b", "main");
  const base = commitAll(root, "base");
  write(root, "src/app.py", "two\n"); // committed below
  commitAll(root, "change src");
  write(root, "docs/guide.md", "two\n"); // unstaged
  write(root, "docs/new.md", "new\n"); // untracked
  // Evidence written without the .gitignore the tool adds, so git reports it and the filter is what skips it.
  write(root, "verification/evidence/area/20250101T000000Z.md", "old evidence\n");
  const result = verify(root, ["affected", base]);
  assert.deepEqual(result, {
    code: 0,
    stdout: [
      `3 path(s) changed since ${base}`,
      "",
      "Recipes these changes touch:",
      "  area  feature",
      "  everything  suite  (the whole tree)",
      "",
      "Changed paths no recipe covers:",
      "  docs/guide.md",
      "  docs/new.md",
      "(everything covers the whole tree: it runs for these, and checks none of them in particular.)",
      "",
    ].join("\n"),
    stderr: "",
  });
});

test("affected lists a whole-tree recipe as touched while every path stays uncovered", (t) => {
  const root = fixture(t, { "verification/recipes/everything.md": AFFECTED_RECIPES["verification/recipes/everything.md"], "lib/x.py": "" });
  git(root, "init", "--quiet", "-b", "main");
  const base = commitAll(root, "base");
  write(root, "lib/x.py", "changed\n");
  const result = verify(root, ["affected", base]);
  assert.equal(result.code, 0);
  assert.equal(
    result.stdout,
    [
      `1 path(s) changed since ${base}`,
      "",
      "Recipes these changes touch:",
      "  everything  suite  (the whole tree)",
      "",
      "Changed paths no recipe covers:",
      "  lib/x.py",
      "(everything covers the whole tree: it runs for these, and checks none of them in particular.)",
      "",
    ].join("\n"),
  );
});

test("affected counts a changed recipe as touching itself", (t) => {
  const root = fixture(t, { "verification/recipes/area.md": AFFECTED_RECIPES["verification/recipes/area.md"], "src/app.py": "" });
  git(root, "init", "--quiet", "-b", "main");
  const base = commitAll(root, "base");
  write(root, "verification/recipes/area.md", `${read(root, "verification/recipes/area.md")}\nMore.\n`);
  const result = verify(root, ["affected", base]);
  assert.equal(result.stdout, `1 path(s) changed since ${base}\n\nRecipes these changes touch:\n  area  feature\n`);
});

test("affected without a base compares with upstream/main before main", (t) => {
  const root = fixture(t, { ...AFFECTED_RECIPES, "src/app.py": "one\n" });
  git(root, "init", "--quiet", "-b", "main");
  const first = commitAll(root, "first");
  write(root, "src/app.py", "two\n");
  const second = commitAll(root, "second");
  // main is at the tip, so comparing with it would find nothing; upstream/main lags one commit.
  git(root, "update-ref", "refs/remotes/upstream/main", first);
  git(root, "checkout", "--quiet", "-b", "feature");
  assert.notEqual(first, second);
  const result = verify(root, ["affected"]);
  assert.equal(result.code, 0);
  assert.equal(
    result.stdout.split("\n").slice(0, 4).join("\n"),
    `1 path(s) changed since where this branch left upstream/main (${first.slice(0, 12)})\n\nRecipes these changes touch:\n  area  feature`,
  );
});

test("affected refuses a base that is not a commit, and a project outside git", (t) => {
  const root = fixture(t, AFFECTED_RECIPES);
  assert.deepEqual(verify(root, ["affected", "HEAD"]), {
    code: 1,
    stdout: "",
    stderr: "verify: affected compares with git history; run it inside a repository\n",
  });
  git(root, "init", "--quiet", "-b", "main");
  commitAll(root, "base");
  assert.deepEqual(verify(root, ["affected", "no-such-ref"]), {
    code: 2,
    stdout: "",
    stderr: "verify: affected: 'no-such-ref' is not a commit here; name a branch, tag or commit\n",
  });
});

// --- drive ------------------------------------------------------------------------------

const DRIVE_RECIPE = recipe(
  "kind: feature",
  [
    "### pass\nRun: `echo all good`\nProves: the passing path passes.",
    "### fail\nRun: `echo \"broke in $PWD\"; exit 1`\nProves: a failure is failed.",
    "### unreach\nRun: `echo 'needs a tool' 1>&2; exit 3`\nProves: a missing prerequisite is unreachable.",
    "### judged\nRun: `echo look at me`\nProves: a person reads it.\nCheck: read",
  ].join("\n\n"),
);

const DRIVE_ENV = { VERIFY_STAMP: STAMP, VERIFY_DURATION: "1.5", VERIFY_MACHINE: "test machine" };

function read(root: string, path: string): string {
  return readFileSync(join(root, path), "utf8");
}

/** The summary a run writes, as the tool lays it out. */
function summary(scenario: string, stamp: string, command: string, code: number, outcome: string, proves: string, output: string): string {
  return [
    `# drv / ${scenario} — ${stamp}`,
    "",
    `- **Scenario:** ${scenario}`,
    `- **Command:** \`${command}\``,
    `- **Exit code:** ${code}`,
    `- **Outcome:** ${outcome}`,
    "- **Run:** test-run",
    "- **Machine:** test-machine",
    "- **Duration:** 1.5 s",
    `- **Proves:** ${proves}`,
    "",
    "## Output",
    "",
    output,
    "",
  ].join("\n");
}

/** The files a recipe's evidence folder holds, hidden ones included. */
function evidenceFiles(root: string, name: string): string[] {
  return readdirSync(join(root, "verification", "evidence", name)).sort();
}

test("drive: a scenario exiting 0 passes, exits 0 and records its evidence", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  const result = verify(root, ["drive", "drv", "pass", "--run", "test-run"], DRIVE_ENV);
  assert.deepEqual(result, {
    code: 0,
    stdout: `running [pass] as run test-run: echo all good\nall good\npassed in 1.5 s: evidence in verification/evidence/drv/${STAMP}.md\n`,
    stderr: "",
  });
  assert.equal(
    read(root, `verification/evidence/drv/${STAMP}.md`),
    summary("pass", STAMP, "echo all good", 0, "passed", "the passing path passes.", "all good"),
  );
  assert.deepEqual(evidenceFiles(root, "drv"), [`${STAMP}.md`]);
  assert.equal(
    read(root, "verification/evidence/.gitignore"),
    "# Written by verify: runs keep their output here, on this machine only.\n*\n",
  );
});

test("drive: a scenario exiting 1 fails, exits 1 and keeps its output with local paths removed", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  const result = verify(root, ["drive", "drv", "fail", "--run", "test-run"], DRIVE_ENV);
  assert.equal(result.code, 1);
  assert.equal(result.stderr, "");
  assert.equal(
    result.stdout,
    `running [fail] as run test-run: echo "broke in $PWD"; exit 1\nbroke in ${realpathSync(root)}\nfailed in 1.5 s: evidence in verification/evidence/drv/${STAMP}.md\n`,
  );
  assert.equal(
    read(root, `verification/evidence/drv/${STAMP}.md`),
    summary("fail", STAMP, 'echo "broke in $PWD"; exit 1', 1, "failed", "a failure is failed.", "broke in [local path]"),
  );
  assert.deepEqual(evidenceFiles(root, "drv"), [`${STAMP}.md`]);
});

test("drive: a scenario exiting 3 is unreachable, and the drive exits 1", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  const result = verify(root, ["drive", "drv", "unreach", "--run", "test-run"], DRIVE_ENV);
  // Exit 1, not 3: a drive exits 1 for any scenario that did not pass. The Exit codes paragraph
  // of --help gives exit 3 to the launcher alone and records a scenario's 3 as unreachable.
  assert.deepEqual(result, {
    code: 1,
    stdout: `running [unreach] as run test-run: echo 'needs a tool' 1>&2; exit 3\nunreachable in 1.5 s: evidence in verification/evidence/drv/${STAMP}.md\n`,
    stderr: "needs a tool\n",
  });
  assert.equal(
    read(root, `verification/evidence/drv/${STAMP}.md`),
    summary("unreach", STAMP, "echo 'needs a tool' 1>&2; exit 3", 3, "unreachable", "a missing prerequisite is unreachable.", "needs a tool"),
  );
});

test("drive: a Check: read scenario passes and says its output needs reading", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  const result = verify(root, ["drive", "drv", "judged", "--run", "test-run"], DRIVE_ENV);
  assert.equal(result.code, 0);
  assert.equal(
    result.stdout.split("\n").at(-2),
    `passed in 1.5 s; its output needs reading (Check: read): evidence in verification/evidence/drv/${STAMP}.md`,
  );
  assert.equal(
    read(root, `verification/evidence/drv/${STAMP}.md`),
    summary("judged", STAMP, "echo look at me", 0, "passed; its output needs reading (Check: read)", "a person reads it.", "look at me"),
  );
});

test("drive of a whole recipe runs every scenario, numbers same-second evidence, and exits 1", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  const result = verify(root, ["drive", "drv", "--run", "test-run"], DRIVE_ENV);
  assert.equal(result.code, 1);
  const kept = (n: string): string => read(root, `verification/evidence/drv/${n}.md`);
  assert.match(kept(STAMP), /^- \*\*Outcome:\*\* passed$/m);
  assert.match(kept(`${STAMP}-2`), /^- \*\*Outcome:\*\* failed$/m);
  assert.match(kept(`${STAMP}-3`), /^- \*\*Outcome:\*\* unreachable$/m);
  assert.match(kept(`${STAMP}-4`), /^- \*\*Outcome:\*\* passed; its output needs reading \(Check: read\)$/m);
  // No reservation marker or half-written file is left behind.
  assert.deepEqual(evidenceFiles(root, "drv"), [`${STAMP}-2.md`, `${STAMP}-3.md`, `${STAMP}-4.md`, `${STAMP}.md`]);
});

test("drive keeps one summary per scenario: a newer run replaces the older", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  const later = "20260102T120000Z";
  assert.equal(verify(root, ["drive", "drv", "pass", "--run", "test-run"], DRIVE_ENV).code, 0);
  assert.equal(verify(root, ["drive", "drv", "fail", "--run", "test-run"], DRIVE_ENV).code, 1);
  assert.equal(verify(root, ["drive", "drv", "pass", "--run", "test-run"], { ...DRIVE_ENV, VERIFY_STAMP: later }).code, 0);
  // The first pass is replaced; the fail, another scenario, stays.
  assert.deepEqual(evidenceFiles(root, "drv"), [`${STAMP}-2.md`, `${later}.md`]);
  const shown = verify(root, ["help", "drv"]);
  assert.equal(shown.code, 0);
  assert.match(shown.stdout, new RegExp(`^  pass: passed in 1\\.5 s on test-machine, verification/evidence/drv/${later}\\.md$`, "m"));
  assert.match(shown.stdout, new RegExp(`^  fail: failed in 1\\.5 s on test-machine, verification/evidence/drv/${STAMP}-2\\.md$`, "m"));
  assert.match(shown.stdout, /^  unreach: not run here$/m);
});

test("drive refuses an ask-first recipe without --yes and runs it with --yes", (t) => {
  const root = fixture(t, {
    "verification/recipes/costly.md": recipe("kind: feature\nask-first: it spends quota", "### go\nRun: `echo spent`\nProves: x."),
  });
  assert.deepEqual(verify(root, ["drive", "costly", "--run", "test-run"], DRIVE_ENV), {
    code: 4,
    stdout: "",
    stderr: "verify: costly is ask-first: it spends quota. Run it only when a person runs it or has agreed, then pass --yes.\n",
  });
  assert.equal(existsSync(join(root, "verification", "evidence")), false);
  assert.equal(verify(root, ["drive", "costly", "--yes", "--run", "test-run"], DRIVE_ENV).code, 0);
});

test("drive refuses an unknown scenario, an unknown recipe and a bad planted duration", (t) => {
  const root = fixture(t, { "verification/recipes/drv.md": DRIVE_RECIPE });
  assert.deepEqual(verify(root, ["drive", "drv", "nope"], DRIVE_ENV), {
    code: 1,
    stdout: "",
    stderr: "verify: drv has no scenario 'nope'; its scenarios are pass, fail, unreach and judged\n",
  });
  assert.deepEqual(verify(root, ["drive", "other"], DRIVE_ENV), { code: 1, stdout: "", stderr: "verify: no recipe 'other'. Known: drv\n" });
  assert.deepEqual(verify(root, ["drive", "drv", "pass"], { ...DRIVE_ENV, VERIFY_DURATION: "soon" }), {
    code: 2,
    stdout: "",
    stderr: "verify: VERIFY_DURATION must be a number of seconds, not 'soon'; unset it to time runs by the clock\n",
  });
});
