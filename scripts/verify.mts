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

// verify — this project's one verification harness.
//
// Run `verify --help` for everything: what can be checked, how, which checks a change touches,
// and which to ask about before running. Recipes are Markdown files in the recipes directory;
// this file reads them and never needs editing to add one.
//
// TypeScript with no dependencies, run by Node 22.18 or newer (23.6 or newer on Node 23),
// which strips the types itself.
// `verify` beside this file starts it and says so when Node is missing or too old.
//
// Adapted for Apache Hamilton from the default harness of manifest-dev 14.20.1: recipes and
// settings open with the ASF license as an HTML comment, which the repository's insert-license
// hook requires of every Markdown file, so front matter is read after that comment; `affected`
// compares with upstream/main first, because contributors push to a fork named origin; a
// front-matter error names its file, and a key the harness does not read is refused, so a
// misspelled `ask-first` cannot pass for a recipe that needs no agreement; and the help says which
// exit 3 is the launcher's own.

import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { randomBytes } from "node:crypto";
import { closeSync, existsSync, fstatSync, mkdirSync, mkdtempSync, openSync, readdirSync, readFileSync, readSync, realpathSync, renameSync, rmSync, statSync, writeFileSync } from "node:fs";
import { arch, availableParallelism, constants, homedir, platform, tmpdir } from "node:os";
import { isAbsolute, join, relative, resolve } from "node:path";

// Where the harness keeps its data. A project that moves it changes these lines.
const ROOT = resolve(process.env.VERIFY_ROOT || join(import.meta.dirname, ".."));
const DATA = resolve(process.env.VERIFY_DATA || join(ROOT, "verification"));
const RECIPES = join(DATA, "recipes");
// What runs write, kept on this machine only: the tool has git ignore it.
const EVIDENCE = join(DATA, "evidence");
const SETTINGS = join(DATA, "harness.md");

const EXIT_UNREACHABLE = 3; // a scenario command exits 3 when a prerequisite is missing
const EXIT_ASK_FIRST = 4; // this harness refused a run that needs a person's agreement without --yes
const EXIT_USAGE = 2;

/** What one run of a scenario came to. A recipe has no status: each run says what it found. */
type Outcome = "passed" | "failed" | "unreachable";

// Commands a project may declare in its settings to control what it checks. Each one runs
// through `verify <name>`; an undeclared one does not exist for that project.
const CONTROL = {
  start: "start an instance of what the project checks, in a known state, for this run",
  running: "say what instances are running",
  logs: "show an instance's logs and traces",
  reset: "put an instance back in its known state",
  stop: "stop an instance this harness started",
} as const;
type Control = keyof typeof CONTROL;
// Own keys only: `in` would also match what every object inherits, such as `toString`.
const isControl = (name: string): name is Control => Object.hasOwn(CONTROL, name);
// Control commands that act on an instance an earlier invocation started, so they name it.
const NAMES_A_RUN: readonly Control[] = ["logs", "reset", "stop"];

const STAMP = /(\d{8}T\d{6}Z)(?:-(\d+))?/;
// Fields earlier versions read for time lines, which were removed: a run reports its duration
// and nothing compares it. A leftover field is refused, so it cannot read as live.
const REMOVED_SCENARIO_FIELDS = ["Line", "Workload"] as const;
const REMOVED_SETTINGS = ["headroom", "raise"] as const;
const REMOVED_WHY = "time lines were removed from the harness, so nothing reads it; delete it";
const REMOVED_FIELD = new RegExp(`^(?:${REMOVED_SCENARIO_FIELDS.join("|")}):.*$`, "gm");
// The front-matter keys each file is read for; any other key is refused rather than ignored.
const RECIPE_KEYS = ["kind", "covers", "ask-first", "dry-run"] as const;
const SETTINGS_KEYS = ["ask-first", "grace", "doctor", ...Object.keys(CONTROL)] as const;
// The branches `affected` tries when given no base: the Apache repository's main when it is a
// remote named upstream (contributors push to a fork named origin, whose main can lag), then
// origin/HEAD, then the rest in order.
const UPSTREAM_BRANCH = "upstream/main";
const DEFAULT_BRANCHES = ["origin/main", "origin/master", "main", "master"];
/** How long a failed run waits on the project's `logs:` command before giving up on it. */
const LOGS_TIMEOUT_SECONDS = 60;
/** How much a `logs:` command may print before it is stopped, so it cannot fill the disk. */
const LOGS_MAX_BYTES = 64 * 1024 * 1024;
// A failure's logs keep their end, where the failure is, and say where they were cut.
const LOGS_TAIL_LINES = 200;
const LOGS_TAIL_CHARS = 64 * 1024;

class Problem extends Error {
  readonly code: number;
  constructor(message: string, code = 1) {
    super(message);
    this.code = code;
  }
}

interface Scenario {
  name: string;
  run: string;
  proves: string;
  judged: boolean; // true: a person or agent reads the output; false: the exit code decides
}

interface Recipe {
  name: string;
  path: string;
  kind: string;
  covers: string[];
  askFirst: string; // the reason, or "" for a recipe that runs freely
  dryRun: boolean; // its commands honor VERIFY_DRY_RUN=1
  scenarios: Scenario[];
  body: string;
}

const read = (path: string): string => readFileSync(path, "utf8");
const seconds = (value: number): string => `${value.toFixed(1)} s`;
const rel = (path: string): string => {
  const inside = relative(ROOT, path);
  return inside && !inside.startsWith("..") && !isAbsolute(inside) ? inside : path;
};
const markdownIn = (folder: string): string[] =>
  existsSync(folder) && statSync(folder).isDirectory()
    ? readdirSync(folder).filter((name) => name.endsWith(".md")).sort().map((name) => join(folder, name))
    : [];
const stem = (path: string): string => path.slice(path.lastIndexOf("/") + 1).replace(/\.md$/, "");
const escapeRegExp = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * Paths that exist only on the machine that ran: this user's home and the temporary directory
 * wherever they are, and the usual places for them elsewhere. Kept output carries none, so it can
 * be quoted where others read it.
 */
function localPaths(): RegExp {
  const places = new Set(["/tmp", "/Users", "/private", "/var/folders"]);
  for (const place of [homedir(), tmpdir()]) {
    if (!place || place === "/") continue;
    places.add(place.replace(/\/+$/, ""));
    try {
      places.add(realpathSync(place).replace(/\/+$/, ""));
    } catch {
      // a home or temporary directory that does not exist has no other spelling
    }
  }
  const longestFirst = [...places].sort((a, b) => b.length - a.length).map(escapeRegExp);
  // `~/…`, `/home/<user>/…`, or one of the places above, alone or followed by a path.
  return new RegExp(
    `\`?(?:~\\/[^\\s\`]*|\\/home\\/[^/\\s\`]+(?:\\/[^\\s\`]*)?|(?:${longestFirst.join("|")})(?![\\w.-])(?:\\/[^\\s\`]*)?)\`?`,
    "g",
  );
}

/**
 * `key: value` lines between `---` fences, and the body after them. A leading `<!-- … -->`
 * comment, the license header every Markdown file here carries, and the blank lines after it are
 * skipped first, and are part of neither.
 */
function frontMatter(whole: string, file: string): [Record<string, string>, string] {
  const header = /^\s*<!--[\s\S]*?-->[ \t]*\n\s*/.exec(whole);
  const text = header ? whole.slice(header[0].length) : whole;
  if (!text.startsWith("---\n")) return [{}, text];
  const end = text.indexOf("\n---\n", 3);
  if (end < 0) throw new Problem(`${file}: front matter has no closing \`---\``);
  const meta: Record<string, string> = {};
  for (const line of text.slice(4, end).split("\n")) {
    if (!line.trim()) continue;
    const colon = line.indexOf(":");
    if (colon < 0) throw new Problem(`${file}: front matter line is not \`key: value\`: ${JSON.stringify(line)}`);
    meta[line.slice(0, colon).trim()] = line.slice(colon + 1).trim();
  }
  return [meta, text.slice(end + 5)];
}

/** One problem per front-matter key outside `known`, naming the keys the file is read for. */
function unknownKeys(meta: Record<string, string>, known: readonly string[], file: string): string[] {
  return Object.keys(meta)
    .filter((key) => !known.includes(key))
    .map((key) => `${file}: front matter has \`${key}:\`, which the harness does not read; it reads ${known.join(", ")}`);
}

function parseRecipe(path: string): Recipe {
  const file = stem(path) + ".md";
  const [meta, body] = frontMatter(read(path), file);
  const unknown = unknownKeys(meta, RECIPE_KEYS, file);
  if (unknown.length) throw new Problem(unknown.join("\n"));
  if (!meta.kind) throw new Problem(`${file}: front matter has no \`kind:\``);
  if (!/^# \S/m.test(body)) throw new Problem(`${file}: no \`# Title\` line`);
  const scenarios: Scenario[] = [];
  const leftovers: string[] = [];
  const section = /^## Scenarios[ \t]*$([\s\S]*?)(?=^## |(?![\s\S]))/m.exec(body);
  for (const block of section ? (section[1] ?? "").split(/^### /m).slice(1) : []) {
    const newline = block.indexOf("\n");
    const name = (newline < 0 ? block : block.slice(0, newline)).trim();
    const rest = newline < 0 ? "" : block.slice(newline);
    const run = /^Run:\s*`([^`]+)`/m.exec(rest);
    const proves = /^Proves:\s*(.+)$/m.exec(rest);
    const check = /^Check:\s*(\S+)/m.exec(rest);
    for (const [left] of rest.matchAll(REMOVED_FIELD)) {
      leftovers.push(`${file}: scenario '${name}' carries \`${left.trim()}\`: ${REMOVED_WHY}`);
    }
    // A leftover found so far is named with the problem that stops the parse, not lost behind it.
    const stop = (problem: string): Problem => new Problem([...leftovers, problem].join("\n"));
    if (!run?.[1]) throw stop(`${file}: scenario '${name}' has no Run: \`command\` line`);
    if (check && check[1] !== "read" && check[1] !== "exit") {
      throw stop(`${file}: scenario '${name}' Check: must be \`read\` or \`exit\``);
    }
    scenarios.push({ name, run: run[1], proves: proves?.[1]?.trim() ?? "", judged: check?.[1] === "read" });
  }
  if (leftovers.length) throw new Problem(leftovers.join("\n"));
  return {
    name: stem(path),
    path,
    kind: meta.kind,
    covers: (meta.covers ?? "").split(",").map((c) => c.trim()).filter(Boolean),
    askFirst: meta["ask-first"] ?? "",
    dryRun: meta["dry-run"] === "honored",
    scenarios,
    body,
  };
}

function recipes(): Recipe[] {
  if (!existsSync(RECIPES)) throw new Problem(`no recipes directory at ${RECIPES}`);
  return markdownIn(RECIPES).map(parseRecipe);
}

function find(name: string): Recipe {
  const path = join(RECIPES, `${name}.md`);
  if (!existsSync(path)) {
    throw new Problem(`no recipe '${name}'. Known: ${recipes().map((r) => r.name).join(", ")}`);
  }
  return parseRecipe(path);
}

interface Settings {
  askFirst: "ask" | "run";
  doctor: string;
  control: Partial<Record<Control, string>>;
  grace: number; // seconds between SIGTERM and SIGKILL when a run is stopped
  notes: string;
}

function settings(): Settings {
  const [meta, body] = existsSync(SETTINGS) ? frontMatter(read(SETTINGS), rel(SETTINGS)) : [{}, ""];
  const leftovers = REMOVED_SETTINGS.filter((key) => Object.hasOwn(meta, key));
  if (leftovers.length) {
    throw new Problem(leftovers.map((key) => `${rel(SETTINGS)}: carries \`${key}: ${meta[key]}\`: ${REMOVED_WHY}`).join("\n"));
  }
  const unknown = unknownKeys(meta, SETTINGS_KEYS, rel(SETTINGS));
  if (unknown.length) throw new Problem(unknown.join("\n"));
  const askFirst = meta["ask-first"] ?? "ask";
  if (askFirst !== "ask" && askFirst !== "run") {
    throw new Problem(`${rel(SETTINGS)}: ask-first must be \`ask\` or \`run\`, not '${askFirst}'`);
  }
  const grace = meta.grace ?? "2";
  if (!/^\d+(?:\.\d+)?$/.test(grace)) {
    throw new Problem(`${rel(SETTINGS)}: grace must be a number of seconds, such as \`2\` or \`0.5\`, not '${grace}'`);
  }
  const control: Partial<Record<Control, string>> = Object.create(null);
  for (const name of Object.keys(CONTROL) as Control[]) {
    if (meta[name]) control[name] = meta[name];
  }
  return {
    askFirst,
    doctor: meta.doctor ?? "",
    control,
    grace: Number(grace),
    notes: body.trim(),
  };
}

/** The kind of machine a run's duration was measured on, recorded beside it so the time reads in context. */
function machineKind(): string {
  const named = process.env.VERIFY_MACHINE?.trim();
  return named ? named.replace(/\s+/g, "-") : `${platform()}-${arch()}-${availableParallelism()}cpu`;
}

/**
 * This invocation's run identity, handed to every command it starts as VERIFY_RUN_ID, so data
 * directories, ports and containers can be per run. `--run ID` names an earlier run's instance;
 * a command started inside a run inherits that run's identity.
 */
function runIdentity(named: string | undefined, needed?: string): string {
  const id = named ?? process.env.VERIFY_RUN_ID;
  if (id !== undefined) {
    if (!/^[A-Za-z0-9][\w.-]*$/.test(id)) {
      const from = named === undefined ? "VERIFY_RUN_ID, inherited from the environment," : `run id '${id}'`;
      throw new Problem(`${from} must be letters, digits, '.', '_' or '-'${named === undefined ? `; it is '${id}'` : ""}`, EXIT_USAGE);
    }
    return id;
  }
  // A fresh identity names no instance, so a command meant for one would act on nothing.
  if (needed) throw new Problem(`verify ${needed}: name the instance with --run ID, the id \`verify start\` printed`, EXIT_USAGE);
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "").replace("T", "-");
  return `${stamp}-${randomBytes(3).toString("hex")}`;
}

const withRun = (id: string, extra: Record<string, string> = {}): NodeJS.ProcessEnv => ({
  ...process.env,
  ...extra,
  VERIFY_RUN_ID: id,
});

// --- local evidence ---------------------------------------------------------------------

/** What a run wrote, read back from its summary's header. */
interface Summary {
  path: string;
  when: string; // the stamp, which sorts as the runs were written within one second's order
  order: number; // the -N suffix of runs stamped in the same second; 1 for the first
  scenario: string;
  outcome: string;
  machine: string;
  duration: number | undefined; // seconds
}

/** A file's text, or undefined when a run beside this one removed it while this one listed it. */
function readIfThere(path: string): string | undefined {
  try {
    return read(path);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
    throw error;
  }
}

/** Write a whole file at once, so a run beside this one never reads it half written. */
function writeWhole(path: string, text: string): void {
  const part = join(path, "..", `.${stem(path)}.${process.pid}.partial`);
  writeFileSync(part, text);
  renameSync(part, path);
}

/**
 * A summary's fields, read from its header only — above its first `## ` section — so a
 * scenario whose output prints a field never sets one. Undefined for a file that is not a
 * finished summary: another file kept beside them, or a run that never finished writing.
 */
function readSummary(path: string): Summary | undefined {
  const stamp = STAMP.exec(stem(path));
  const text = stamp ? readIfThere(path) : undefined;
  if (!stamp?.[1] || !text?.trim()) return undefined;
  const at = text.search(/^## /m);
  const head = at < 0 ? text : text.slice(0, at);
  const field = (name: string): string => new RegExp(`^- \\*\\*${name}:\\*\\* (.+)$`, "m").exec(head)?.[1]?.trim() ?? "";
  const duration = /^(\d+(?:\.\d+)?) s$/.exec(field("Duration"))?.[1];
  return {
    path,
    when: stamp[1],
    order: Number(stamp[2] ?? 1),
    scenario: field("Scenario"),
    outcome: /^\w+/.exec(field("Outcome"))?.[0] ?? "",
    machine: field("Machine"),
    duration: duration === undefined ? undefined : Number(duration),
  };
}

const older = (a: Summary, b: Summary): number => a.when.localeCompare(b.when) || a.order - b.order;

/** The summaries this machine keeps for a recipe, oldest first. */
function summariesFor(recipe: Recipe): Summary[] {
  return markdownIn(join(EVIDENCE, recipe.name))
    .map(readSummary)
    .filter((s): s is Summary => s !== undefined)
    .sort(older);
}

/** The latest run of a scenario on this machine, or undefined when it has not run here. */
function latestRun(recipe: Recipe, scenario: string): Summary | undefined {
  return summariesFor(recipe).filter((s) => s.scenario === scenario).at(-1);
}

/**
 * A recipe's folder in the evidence directory, made on first use. The evidence directory ignores
 * itself in git, so what runs write stays on this machine and nothing asks to commit it.
 */
function evidenceFolder(recipe: Recipe): string {
  mkdirSync(EVIDENCE, { recursive: true });
  try {
    writeFileSync(join(EVIDENCE, ".gitignore"), "# Written by verify: runs keep their output here, on this machine only.\n*\n", { flag: "wx" });
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
  }
  const folder = join(EVIDENCE, recipe.name);
  mkdirSync(folder, { recursive: true });
  return folder;
}

// --- commands ---------------------------------------------------------------------------

const HELP = `verify — this project's one place to control what it checks and to check that its
work still does its job.

recipes:  {recipes}
settings: {settings}
evidence: {evidence} (what runs write, on this machine only; git ignores it)

Every check is a recipe: a Markdown file in the recipes directory naming what it covers, how a
user reaches it, the scenarios that exercise it (each a command and what it proves), and its
traps. This tool lists them, names the ones a change touches, and runs them. It is a default shape
for a harness: adapt it, its settings or its recipes wherever this project is better served
another way, and say so here.

Commands:
  verify list [KIND]          every recipe with its kind and ask-first mark
  verify help RECIPE          one recipe in full, with each scenario's latest run here
  verify drive RECIPE [SCENARIO] [--yes] [--dry-run] [--run ID]
                              run a recipe's scenarios (all, or the one named)
  verify walk RECIPE ...      the same, for a recipe of kind walk
  verify eval RECIPE ...      the same, for a recipe of kind eval
  verify affected [BASE]      the recipes a change since BASE touches, which are the ones to run,
                              and the changed paths no recipe covers. Without BASE: since the
                              branch left the default branch (${UPSTREAM_BRANCH}, else origin/HEAD,
                              else ${DEFAULT_BRANCHES.join(", ")})
  verify doctor               check the harness's prerequisites (free; starts nothing costly)
  verify check                check every recipe parses and names only paths that exist
{control}
When to run it: before saying a change works, when reproducing a reported problem, and when a
change touches what a recipe covers (\`verify affected\` names them). A change that needs a check
no recipe has adds the recipe. Every check without the ask-first mark is free: run it as often as
it helps.

Ask first: a recipe marked ask-first costs something a person should weigh — money or quota,
load on shared systems or other teams, effects outside this repository. Run time alone is not a
cost. Its reason is shown in \`verify help RECIPE\`. This project's setting: ask-first = {policy}.
  ask  run an ask-first recipe only when a person runs it or has agreed — in the session, or by
       approving a plan whose check runs it: ask first, naming the recipe and why; then pass --yes
  run  run them freely
Change it in {settings}. Recipes without the mark run freely.

Run identity: every command this tool starts gets VERIFY_RUN_ID, one per invocation, so data
directories, ports and containers can be per run and runs can go side by side. \`--run ID\` on a
drive or a control command reaches the instance an earlier run started (\`verify start\` prints its
id); logs, reset and stop need it. A command started inside a run inherits that run's identity.
A control command for an id its instance does not know exits non-zero, saying so.

Run time: every run prints and records how long it took, and that is the only time signal. Keep
checks fast and treat a slow one as friction to fix, never by checking less; no run blocks, fails
or exits non-zero because of how long it took. Set VERIFY_MACHINE to name the kind of machine the
summary records beside the duration, such as a CI runner label. VERIFY_DURATION stands in for
every measured time, for the tool's own tests; leave it unset.

Evidence: each run writes {evidence}/RECIPE/STAMP.md (command, exit code, outcome, run identity,
kind of machine, duration, output with local paths removed) and removes that scenario's older
one, so a failure explains itself in the run that met it. When a run fails and the project
declares \`logs:\`, its output for that run is kept too. It stays on this machine: the evidence
directory ignores itself in git, so nothing a run writes is committed. Whatever a command started
is stopped when it ends: SIGTERM, then SIGKILL after {grace} s (\`grace:\` in {settings}). An
interrupted run keeps no evidence; a command that crashes is failed.

Exit codes: 0 done; 1 a scenario failed, was unreachable or could not start, or a problem;
2 usage; 3 Node is missing or too old (the launcher); 4 refused without a person's agreement
(--yes). A scenario command exits 3 when a prerequisite is missing, and its run is recorded as
unreachable. A control command exits with its project command's own code.

Adding a recipe: copy any file in {recipes}, keep the front matter keys (kind, covers,
ask-first when it applies, dry-run: honored when its commands obey VERIFY_DRY_RUN=1), and give
each scenario a \`### name\` heading with \`Run:\`, \`Proves:\` and, when the exit code cannot decide,
\`Check: read\`: a run then passes on its exit code and its output still needs reading. A
\`covers: .\` recipe runs for every change and covers no path in particular. \`verify check\`
validates it.
`;

function cmdHelp(): number {
  const conf = settings();
  const declared = (Object.keys(CONTROL) as Control[]).filter((name) => conf.control[name]);
  const control = declared.length
    ? `\nControl (this project's commands, declared in {settings}):\n` +
      declared.map((name) => `  verify ${`${name}${name === "running" ? "" : " [--run ID]"}`.padEnd(24)}${CONTROL[name]}: ${conf.control[name]}\n`).join("")
    : "";
  const fill: Record<string, string> = {
    recipes: rel(RECIPES),
    evidence: rel(EVIDENCE),
    settings: rel(SETTINGS),
    policy: conf.askFirst,
    grace: String(conf.grace),
  };
  const text = HELP.replace("{control}", control);
  console.log(text.replace(/\{(\w+)\}/g, (whole, key: string) => fill[key] ?? whole));
  if (conf.notes) console.log(`This project's notes:\n\n${conf.notes}`);
  console.log(`\nRecipes: ${recipes().length}. Run \`verify list\` to see them.`);
  return 0;
}

function cmdList(kind: string | undefined): number {
  const rows = recipes()
    .filter((r) => kind === undefined || r.kind === kind)
    .map((r) => [r.name, r.kind, r.askFirst ? "ask-first" : ""] as const);
  if (!rows.length) throw new Problem(`no recipes of kind '${kind}'; \`verify list\` shows every kind`);
  const width = (i: 0 | 1): number => Math.max(...rows.map((row) => row[i].length));
  for (const [name, rkind, mark] of rows) {
    console.log(`${name.padEnd(width(0))}  ${rkind.padEnd(width(1))}  ${mark}`.trimEnd());
  }
  return 0;
}

function cmdShow(name: string): number {
  const recipe = find(name);
  console.log(`${rel(recipe.path)} — ${recipe.kind}`);
  if (recipe.askFirst) console.log(`ask-first: ${recipe.askFirst}`);
  console.log(recipe.body.trim());
  console.log("\nThe latest run on this machine, per scenario:");
  for (const scenario of recipe.scenarios) {
    const last = latestRun(recipe, scenario.name);
    const took = last?.duration !== undefined ? ` in ${seconds(last.duration)} on ${last.machine}` : "";
    console.log(`  ${scenario.name}: ${last ? `${last.outcome}${took}, ${rel(last.path)}` : "not run here"}`);
  }
  return 0;
}

/**
 * A fresh evidence name, held by a marker until the summary is written over it: two runs
 * started in the same second each get their own. Returns the summary's path, its stamp and
 * the marker to remove once the run ends.
 */
function reserve(recipe: Recipe): [string, string, string] {
  const folder = evidenceFolder(recipe);
  const stamp = process.env.VERIFY_STAMP || new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
  // After the run it replaces, not into a name that run freed: a reused name would sort first.
  const taken = readdirSync(folder)
    .map((name) => new RegExp(`^\\.?${stamp}(?:-(\\d+))?\\.(?:md|reserved)$`).exec(name))
    .filter((m): m is RegExpExecArray => m !== null)
    .map((m) => Number(m[1] ?? 1));
  for (let n = Math.max(0, ...taken) + 1; ; n++) {
    const candidate = n === 1 ? stamp : `${stamp}-${n}`;
    const path = join(folder, `${candidate}.md`);
    const marker = join(folder, `.${candidate}.reserved`);
    try {
      writeFileSync(marker, `${process.pid}\n`, { flag: "wx" });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
      continue;
    }
    if (!existsSync(path)) return [path, candidate, marker];
    rmSync(marker, { force: true });
  }
}

interface Run {
  code: number;
  output: string;
  interrupted: boolean;
  seconds: number;
}

/** Signals that stop a run: Ctrl-C, a polite kill, a closed terminal, Ctrl-\. */
const STOP_SIGNALS: NodeJS.Signals[] = ["SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT"];

/** Send a signal to a process group that may already be gone. */
function signalGroup(pid: number, signal: NodeJS.Signals): void {
  try {
    process.kill(-pid, signal);
  } catch {
    // the group already ended
  }
}

/** Hand a command's process group to its watchdog to stop, by closing the watchdog's pipe. */
function stop(child: ChildProcess): void {
  child.stdio[3]?.destroy();
}

function stopping(child: ChildProcess): boolean {
  return child.stdio[3]?.destroyed === true;
}

/**
 * Ctrl-C and termination while a scenario runs. Installed before a run reserves its evidence
 * file, so a signal at any point leaves that file to be removed rather than killing the tool.
 * The first signal is passed on to the running command's process group. A second hands the
 * group to its watchdog to stop; one more, or a signal once the command's shell is gone, kills
 * the group at once. A group still in its grace when the tool exits is left to its watchdog.
 */
class Interrupts {
  interrupted = false;
  child: ChildProcess | undefined;
  private readonly handle = (signal: NodeJS.Signals): void => {
    const child = this.child;
    if (child?.pid !== undefined) {
      if (stopping(child)) signalGroup(child.pid, "SIGKILL");
      else if (this.interrupted) stop(child);
      else signalGroup(child.pid, signal);
    }
    this.interrupted = true;
  };
  constructor() {
    for (const signal of STOP_SIGNALS) process.on(signal, this.handle);
  }
  release(): void {
    for (const signal of STOP_SIGNALS) process.off(signal, this.handle);
  }
}

/**
 * Runs the scenario command in a process group of its own beside a watchdog that stops the
 * group: SIGTERM, which a container client passes on to the session inside, then SIGKILL for
 * whatever outlasts the grace. It waits on descriptor 3, a pipe whose other end only this tool
 * holds, and stops the group when that end closes: when this tool closes it (the command's
 * shell has ended, or a stop was asked for), and when this tool is gone, however it died, even
 * before anyone reaps it. So a command never outlives the tool, and what it leaves behind is
 * stopped even if the tool dies during the grace. The watchdog ignores the SIGTERM and SIGHUP a
 * stop sends. The command's shell then replaces the one that started the watchdog, so the process
 * this tool watches is the command's own: a signal passed on to it ends the run only once the
 * command's shell has finished with it, and no stop starts while that shell is still cleaning up.
 * A child of a shell that does not handle the signal is stopped with the rest of the group once
 * the shell has died of it. The command does not inherit the descriptor, and its exit status is
 * the run's.
 */
const watched = (grace: number): string =>
  [
    `( trap '' TERM HUP; read -r _ <&3; kill -TERM 0; sleep ${grace}; kill -KILL 0 ) </dev/null >/dev/null 2>&1 &`,
    'exec sh -c "$VERIFY_COMMAND" 3<&-',
  ].join("\n");

// Output keeps being collected when whoever reads this tool's output goes away (`| head`).
let echo = true;
for (const stream of [process.stdout, process.stderr]) {
  stream.on("error", (error: NodeJS.ErrnoException) => {
    if (error.code !== "EPIPE") throw error;
    echo = false;
  });
}

/** Run a scenario's command, showing its output as it arrives and keeping a copy. */
function runShown(command: string, interrupts: Interrupts, env: NodeJS.ProcessEnv, grace: number): Promise<Run> {
  return new Promise((done, fail) => {
    const began = performance.now();
    // Scenario commands take no input: they run unattended, in a process group of their own.
    const child = spawn("sh", ["-c", watched(grace)], {
      cwd: ROOT,
      detached: true,
      stdio: ["ignore", "pipe", "pipe", "pipe"],
      env: { ...env, VERIFY_COMMAND: command },
    });
    interrupts.child = child;
    const [, stdout, stderr] = child.stdio;
    if (!stdout || !stderr) throw new Error("the command's output pipes were not opened");
    const chunks: Buffer[] = [];
    stdout.on("data", (chunk: Buffer) => {
      chunks.push(chunk);
      if (echo) process.stdout.write(chunk);
    });
    stderr.on("data", (chunk: Buffer) => {
      chunks.push(chunk);
      if (echo) process.stderr.write(chunk);
    });
    child.on("error", fail);
    // The command's shell is gone, however it ended: stop what it left behind (a background job
    // still holding the output), so the run can end and nothing outlives it.
    child.on("exit", () => stop(child));
    child.on("close", (code, signal) => {
      interrupts.child = undefined;
      done({
        // A command that died by a signal nobody sent here failed, the way a shell reports it.
        code: code ?? 128 + (signal ? constants.signals[signal] : 0),
        // Invalid UTF-8 becomes U+FFFD rather than stopping the run.
        output: Buffer.concat(chunks).toString("utf8"),
        interrupted: interrupts.interrupted,
        seconds: (performance.now() - began) / 1000,
      });
    });
  });
}

/** "a, b and c": the scenarios a recipe has, for a message naming one it does not. */
function scenarioNames(recipe: Recipe): string {
  const names = recipe.scenarios.map((s) => s.name);
  return names.length > 1 ? `${names.slice(0, -1).join(", ")} and ${names.at(-1)}` : (names[0] ?? "none");
}

/**
 * VERIFY_DURATION, when set, stands in for every measured run time, as VERIFY_STAMP stands in for
 * the clock, so a test of what a run records plants a duration rather than waiting it out.
 */
function plantedDuration(): number | undefined {
  const planted = process.env.VERIFY_DURATION;
  if (planted === undefined) return undefined;
  if (!/^\d+(?:\.\d+)?$/.test(planted)) throw new Problem(`VERIFY_DURATION must be a number of seconds, not '${planted}'; unset it to time runs by the clock`, EXIT_USAGE);
  return Number(planted);
}

/** Remove the scenario's summaries older than the one just written, so this machine keeps one. */
function replaceOlder(recipe: Recipe, scenario: string, kept: Summary): void {
  for (const item of summariesFor(recipe)) {
    if (item.path !== kept.path && item.scenario === scenario && older(item, kept) < 0) rmSync(item.path, { force: true });
  }
}

/** The last `bytes` of an open file, how many lines the whole file holds, and whether it held more. */
function tailOf(fd: number, bytes: number): [string, number, boolean] {
  const size = fstatSync(fd).size;
  const chunk = Buffer.alloc(1024 * 1024);
  let lines = 0;
  for (let at = 0; at < size; ) {
    const read = readSync(fd, chunk, 0, chunk.length, at);
    if (read <= 0) break;
    for (let k = 0; k < read; k++) if (chunk[k] === 0x0a) lines++;
    at += read;
  }
  const start = Math.max(0, size - bytes);
  const tail = Buffer.alloc(size - start);
  if (tail.length) readSync(fd, tail, 0, tail.length, start);
  return [tail.toString("utf8"), lines, start > 0];
}

/**
 * The project's `logs:` output for a run, for evidence that has to explain a failure. It goes
 * to a file rather than a pipe, so a process the command leaves running cannot hold the run
 * open; the command runs in its own process group, killed when it ends, times out, prints more
 * than the cap, or the tool is asked to stop. Only the file's end is read back.
 */
async function logsFor(command: string, id: string, scrub: RegExp): Promise<string> {
  const folder = mkdtempSync(join(tmpdir(), "verify-logs-"));
  const file = join(folder, "output");
  const fd = openSync(file, "w+");
  let printed: string;
  let total: number;
  let partial: boolean;
  let ended: string;
  try {
    const child = spawn(command, { shell: true, cwd: ROOT, env: withRun(id), stdio: ["ignore", fd, fd], detached: true });
    let why = "";
    const kill = (reason: string): void => {
      why ||= reason;
      if (child.pid !== undefined) signalGroup(child.pid, "SIGKILL");
    };
    const timer = setTimeout(() => kill(`did not finish within ${LOGS_TIMEOUT_SECONDS} s`), LOGS_TIMEOUT_SECONDS * 1000);
    const watch = setInterval(() => {
      if (fstatSync(fd).size > LOGS_MAX_BYTES) kill(`printed more than ${LOGS_MAX_BYTES / 1024 / 1024} MB and was stopped`);
    }, 250);
    // The command has a process group of its own, so a stop asked of the tool has to reach it here.
    const onStop = (): void => kill("was stopped with the run");
    for (const signal of STOP_SIGNALS) process.on(signal, onStop);
    try {
      const [code, signal] = await new Promise<[number | null, NodeJS.Signals | null]>((done, fail) => {
        child.once("error", fail);
        child.once("exit", (c, s) => done([c, s]));
      });
      ended = why || (code === 0 ? "" : `exited ${code ?? signal}`);
    } finally {
      clearTimeout(timer);
      clearInterval(watch);
      for (const signal of STOP_SIGNALS) process.off(signal, onStop);
      if (child.pid !== undefined) signalGroup(child.pid, "SIGKILL"); // whatever it left running
    }
    [printed, total, partial] = tailOf(fd, LOGS_TAIL_CHARS * 4);
  } finally {
    closeSync(fd);
    rmSync(folder, { recursive: true, force: true });
  }
  const whole = printed.trim();
  let tail = whole.split("\n").slice(-LOGS_TAIL_LINES).join("\n");
  if (tail.length > LOGS_TAIL_CHARS) tail = tail.slice(-LOGS_TAIL_CHARS);
  const shown = tail.split("\n").length;
  const all = Math.max(total + (printed.endsWith("\n") ? 0 : 1), shown);
  const cut = partial || tail.length < whole.length ? ` (its last ${shown} of ${all} lines)` : "";
  const output = tail.replace(scrub, "[local path]") || "(none)";
  const said = ended ? `The logs command \`${command}\` ${ended}; what it printed${cut}:` : `From \`${command}\`${cut}:`;
  return `## Logs\n\n${said.replace(scrub, "[local path]")}\n\n${output}\n`;
}

interface Drive {
  id: string;
  planted: number | undefined;
  machine: string;
  scrub: RegExp;
  conf: Settings;
  interrupts: Interrupts;
}

/**
 * One run of a scenario, keeping its evidence on this machine. Undefined when it was interrupted,
 * which keeps no evidence.
 */
async function runOnce(recipe: Recipe, scenario: Scenario, drive: Drive): Promise<Outcome | undefined> {
  const [path, stamp, marker] = reserve(recipe);
  let written = false;
  try {
    console.log(`running [${scenario.name}] as run ${drive.id}: ${scenario.run}`);
    const run = drive.interrupts.interrupted ? undefined : await runShown(scenario.run, drive.interrupts, withRun(drive.id), drive.conf.grace);
    if (!run || run.interrupted) return undefined;
    const took = drive.planted ?? run.seconds;
    const outcome: Outcome = run.code === EXIT_UNREACHABLE ? "unreachable" : run.code !== 0 ? "failed" : "passed";
    const logs = outcome !== "passed" && drive.conf.control.logs ? `\n${await logsFor(drive.conf.control.logs, drive.id, drive.scrub)}` : "";
    if (drive.interrupts.interrupted) return undefined;
    const reading = scenario.judged && outcome === "passed" ? "; its output needs reading (Check: read)" : "";
    writeWhole(
      path,
      `# ${recipe.name} / ${scenario.name} — ${stamp}\n\n` +
        `- **Scenario:** ${scenario.name}\n` +
        `- **Command:** \`${scenario.run}\`\n` +
        `- **Exit code:** ${run.code}\n` +
        `- **Outcome:** ${outcome}${reading}\n` +
        `- **Run:** ${drive.id}\n` +
        `- **Machine:** ${drive.machine}\n` +
        `- **Duration:** ${seconds(took)}\n` +
        `- **Proves:** ${scenario.proves || "(not stated)"}\n\n` +
        `## Output\n\n${run.output.trim().replace(drive.scrub, "[local path]") || "(none)"}\n` +
        logs,
    );
    written = true;
    const kept = readSummary(path);
    if (kept) replaceOlder(recipe, scenario.name, kept);
    console.log(`${outcome} in ${seconds(took)}${reading}: evidence in ${rel(path)}`);
    return outcome;
  } finally {
    // A run that did not finish leaves nothing behind to pass for evidence.
    if (!written) rmSync(path, { force: true });
    rmSync(marker, { force: true });
  }
}

async function cmdDrive(
  name: string,
  only: string | undefined,
  yes: boolean,
  dry: boolean,
  kind: string | undefined,
  named: string | undefined,
): Promise<number> {
  const recipe = find(name);
  if (kind && recipe.kind !== kind) throw new Problem(`${name} is of kind ${recipe.kind}; use \`verify drive ${name}\``);
  const chosen = recipe.scenarios.filter((s) => only === undefined || s.name === only);
  if (!chosen.length) {
    throw new Problem(only ? `${name} has no scenario '${only}'; its scenarios are ${scenarioNames(recipe)}` : `${name} has no scenarios to run; give it a \`### name\` heading with a \`Run:\` line under \`## Scenarios\``);
  }
  const conf = settings();
  if (recipe.askFirst && conf.askFirst === "ask" && !yes && !dry) {
    throw new Problem(
      `${name} is ask-first: ${recipe.askFirst}. Run it only when a person runs it or has agreed, then pass --yes.`,
      EXIT_ASK_FIRST,
    );
  }
  const id = runIdentity(named);
  const interrupts = new Interrupts();
  const drive: Drive = { id, planted: plantedDuration(), machine: machineKind(), scrub: localPaths(), conf, interrupts };
  const interrupted = (scenario: Scenario): number => {
    console.error(`interrupted: no evidence kept for [${scenario.name}]`);
    return 130;
  };
  let worst = 0;
  try {
    for (const scenario of chosen) {
      if (dry) {
        console.log(`would run [${scenario.name}]: ${scenario.run}`);
        console.log(`evidence:  ${rel(join(EVIDENCE, recipe.name))}/<stamp>.md`);
        if (recipe.dryRun) {
          spawnSync(scenario.run, { shell: true, cwd: ROOT, stdio: "inherit", env: withRun(id, { VERIFY_DRY_RUN: "1" }) });
          // A signal that arrived during the blocking call is handled once the event loop turns.
          await new Promise((resolve) => setImmediate(resolve));
          if (interrupts.interrupted) return 130;
        }
        continue;
      }
      const outcome = await runOnce(recipe, scenario, drive);
      if (!outcome) return interrupted(scenario);
      if (outcome !== "passed") worst = 1;
    }
  } finally {
    interrupts.release();
  }
  return worst;
}

function cmdControl(name: Control, named: string | undefined): number {
  const command = settings().control[name];
  if (!command) {
    throw new Problem(
      `this project declares no \`${name}:\` command; add \`${name}: <command>\` to the front matter of ${rel(SETTINGS)} to ${CONTROL[name]}`,
      EXIT_USAGE,
    );
  }
  const id = runIdentity(named, NAMES_A_RUN.includes(name) ? name : undefined);
  if (name === "start") console.log(`run ${id}: reach this instance later with --run ${id}`);
  const done = spawnSync(command, { shell: true, cwd: ROOT, stdio: "inherit", env: withRun(id) });
  if (done.error) throw done.error;
  return done.status ?? 128 + (done.signal ? constants.signals[done.signal] : 0);
}

/** Paths changed since a base, relative to the project: committed, staged, unstaged and new. */
function changedSince(base: string): string[] {
  const top = git("rev-parse", "--show-toplevel").trim();
  // Relative to the repository's top, which may sit above this project.
  const fromTop = [
    ...git("diff", "--name-only", "-z", "--no-renames", base, "--").split("\0"),
    ...git("ls-files", "-z", "--others", "--exclude-standard", "--full-name").split("\0"),
  ].filter(Boolean);
  // git reports real paths, so a project reached through a link compares by its real path.
  const root = realpathSync(ROOT);
  return [...new Set(fromTop.map((path) => relative(root, join(top, path))))]
    .filter((path) => path && !path.startsWith(".."))
    .sort();
}

/**
 * Where the branch left the default branch: UPSTREAM_BRANCH, else origin/HEAD, else the first of
 * DEFAULT_BRANCHES that exists here.
 */
function defaultBase(): [string, string] {
  const remote = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD").trim();
  for (const branch of [UPSTREAM_BRANCH, remote, ...DEFAULT_BRANCHES].filter(Boolean)) {
    const fork = git("merge-base", "HEAD", branch).trim();
    if (fork) return [fork, `where this branch left ${branch}`];
  }
  // Comparing with the last commit instead would hide everything this branch committed.
  throw new Problem(
    `affected: no default branch to compare with (${UPSTREAM_BRANCH}, origin/HEAD, ${DEFAULT_BRANCHES.join(", ")}); name one: verify affected BASE`,
    EXIT_USAGE,
  );
}

/** Output of a git command in the project, or "" outside a repository or on failure. */
function git(...args: string[]): string {
  const done = spawnSync("git", ["-C", ROOT, ...args], { encoding: "utf8" });
  return done.status === 0 ? done.stdout : "";
}

const insideRepository = (): boolean => git("rev-parse", "--is-inside-work-tree").trim() === "true";

/** True for a path, relative to the project, under the harness's own evidence. */
function isEvidencePath(path: string): boolean {
  const evidence = rel(EVIDENCE);
  return path === evidence || path.startsWith(`${evidence}/`);
}

/** A cover naming the whole tree (`.`): such a recipe runs for every change and covers no path. */
const wholeTree = (cover: string): boolean => ["", "."].includes(cover.replace(/^(?:\.\/)+/, "").replace(/\/+$/, ""));

/** True when the recipe covers the path; a whole-tree cover counts only when `whole` says so. */
function covering(recipe: Recipe, path: string, whole: boolean): boolean {
  return (
    path === rel(recipe.path) ||
    recipe.covers.some((c) => {
      if (wholeTree(c)) return whole;
      const cover = c.replace(/^(?:\.\/)+/, "").replace(/\/+$/, "");
      return path === cover || path.startsWith(`${cover}/`);
    })
  );
}

function cmdAffected(base: string | undefined): number {
  if (!insideRepository()) throw new Problem("affected compares with git history; run it inside a repository");
  const [ref, from] = base === undefined ? defaultBase() : [base, base];
  if (!git("rev-parse", "--verify", "--quiet", `${ref}^{commit}`).trim()) {
    throw new Problem(`affected: '${ref}' is not a commit here; name a branch, tag or commit`, EXIT_USAGE);
  }
  const changed = changedSince(ref).filter((path) => !isEvidencePath(path));
  const all = recipes();
  // A whole-tree recipe runs for every change, so it is among those touched; but it checks no
  // path in particular, so a path only it covers is still one no recipe covers.
  const touched = all.filter((r) => changed.some((path) => covering(r, path, true)));
  const uncovered = changed.filter((path) => !all.some((r) => covering(r, path, false)));
  const whole = touched.filter((r) => r.covers.some(wholeTree));
  console.log(`${changed.length} path(s) changed since ${from}${base === undefined ? ` (${ref.slice(0, 12)})` : ""}`);
  console.log(touched.length ? "\nRecipes these changes touch:" : "\nNo recipe covers these changes.");
  for (const r of touched) {
    console.log(`  ${r.name}  ${r.kind}${r.covers.some(wholeTree) ? "  (the whole tree)" : ""}${r.askFirst ? "  ask-first" : ""}`);
  }
  if (uncovered.length) {
    console.log("\nChanged paths no recipe covers:");
    for (const path of uncovered) console.log(`  ${path}`);
    if (whole.length) {
      console.log(`(${whole.map((r) => r.name).join(", ")} covers the whole tree: it runs for these, and checks none of them in particular.)`);
    }
  }
  return 0;
}

function checkProblems(): string[] {
  const problems: string[] = [];
  try {
    settings();
  } catch (error) {
    if (!(error instanceof Problem)) throw error;
    problems.push(...error.message.split("\n"));
  }
  for (const path of markdownIn(RECIPES)) {
    let recipe: Recipe;
    try {
      recipe = parseRecipe(path);
    } catch (error) {
      if (!(error instanceof Problem)) throw error;
      // One problem per line: a recipe's leftover fields are named together in one message.
      problems.push(...error.message.split("\n"));
      continue;
    }
    const file = `${recipe.name}.md`;
    for (const covered of recipe.covers) {
      if (!existsSync(join(ROOT, covered))) problems.push(`${file}: covers ${covered}, which does not exist`);
    }
    for (const scenario of recipe.scenarios) {
      // A path counts as a reference when its first directory exists here; an output
      // directory a run creates (artifacts/…) does not, and is left alone.
      for (const [token] of scenario.run.matchAll(/(?<![\w/.-])(?:[\w.-]+\/)+[\w.-]+/g)) {
        const top = join(ROOT, token.split("/")[0] ?? "");
        if (existsSync(top) && statSync(top).isDirectory() && !existsSync(join(ROOT, token))) {
          problems.push(`${file}: scenario ${scenario.name} names ${token}, which does not exist`);
        }
      }
    }
  }
  return problems;
}

function cmdCheck(): number {
  const problems = checkProblems();
  for (const problem of problems) console.log(problem);
  console.log(problems.length ? `check: ${problems.length} problem(s)` : "check: ok");
  return problems.length ? 1 : 0;
}

function cmdDoctor(): number {
  const problems = checkProblems();
  let command = "";
  try {
    command = settings().doctor;
  } catch (error) {
    // Settings that do not parse are already among the problems, so there is no command to run.
    if (!(error instanceof Problem)) throw error;
  }
  if (command && spawnSync(command, { shell: true, cwd: ROOT, stdio: "inherit", env: withRun(runIdentity(undefined)) }).status !== 0) {
    problems.push(`doctor command failed: ${command}`);
  }
  for (const problem of problems) console.log(problem);
  console.log(problems.length ? "doctor: not ready" : "doctor: ok");
  return problems.length ? 1 : 0;
}

const USAGE = `usage: verify [--help] {list,help,drive,walk,eval,affected,doctor,check,${Object.keys(CONTROL).join(",")}} ...`;

async function main(argv: string[]): Promise<number> {
  const [command, ...rest] = argv;
  if (command === undefined || command === "-h" || command === "--help") return cmdHelp();
  // `--run ID` (or `--run=ID`) carries a value; every other option is a bare flag.
  const flags = new Set<string>();
  const args: string[] = [];
  let run: string | undefined;
  for (let i = 0; i < rest.length; i++) {
    const arg = rest[i] ?? "";
    if (arg === "--run") {
      flags.add(arg);
      run = rest[++i] ?? "";
    } else if (arg.startsWith("--run=")) {
      flags.add("--run");
      run = arg.slice("--run=".length);
    } else if (arg.startsWith("--")) flags.add(arg);
    else args.push(arg);
  }
  const control = isControl(command) ? command : undefined;
  const allowed = ["drive", "walk", "eval"].includes(command)
    ? ["--yes", "--dry-run", "--run"]
    : control && control !== "running"
      ? ["--run"]
      : [];
  const unknown = [...flags].filter((f) => !allowed.includes(f));
  const arity = (min: number, max: number): void => {
    if (unknown.length || args.length < min || args.length > max || run === "") {
      const why = unknown.length ? `unknown option ${unknown.join(" ")}` : run === "" ? "--run needs a run id" : "wrong number of arguments";
      throw new Problem(`${USAGE}\nverify ${command}: ${why}; see verify --help`, EXIT_USAGE);
    }
  };
  switch (command) {
    case "list":
      arity(0, 1);
      return cmdList(args[0]);
    case "help":
      arity(1, 1);
      return cmdShow(args[0] ?? "");
    case "drive":
    case "walk":
    case "eval":
      arity(1, 2);
      return cmdDrive(args[0] ?? "", args[1], flags.has("--yes"), flags.has("--dry-run"), command === "drive" ? undefined : command, run);
    case "affected":
      arity(0, 1);
      return cmdAffected(args[0]);
    case "doctor":
      arity(0, 0);
      return cmdDoctor();
    case "check":
      arity(0, 0);
      return cmdCheck();
    default:
      if (control) {
        arity(0, 0);
        return cmdControl(control, run);
      }
      throw new Problem(`${USAGE}\nverify: unknown command '${command}'; see verify --help`, EXIT_USAGE);
  }
}

main(process.argv.slice(2)).then(
  (code) => {
    process.exitCode = code;
  },
  (error: unknown) => {
    if (error instanceof Problem) {
      console.error(`verify: ${error.message}`);
      process.exitCode = error.code;
      return;
    }
    // A failure no check above foresaw, such as a file it could not write: say what it was and
    // what to do, never a bare stack.
    const said = error instanceof Error ? error.message : String(error);
    console.error(
      `verify: stopped: ${said}\nFix what this names (a path, a permission, a missing program) and run the command again; ` +
        "if it names nothing you can fix, report it with the command you ran.",
    );
    process.exitCode = 1;
  },
);
