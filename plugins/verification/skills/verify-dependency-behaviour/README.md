# verify-dependency-behaviour

Reads what a third-party library actually does out of the artifact that runs,
instead of trusting its name. A field name, a README and a plausible default are
all claims; the bytecode is what executes, and where they disagree the
disagreement is silent: a "fix" that changes nothing, or a number wrong by a
factor of a hundred.

Read [SKILL.md](SKILL.md) for the procedure. This file is when to reach for it
and what the evidence looks like.

## Using it

Fire it when you are about to state or rely on how a JVM/Android library
behaves and cannot point at evidence:

- a plan says "set X to its strict value" with no proof X is not already strict
- a field's name and its type disagree (`*_percentage` holding a fraction of 1)
- a check passes and you cannot say which comparison it made
- the docs are absent or ambiguous on a default, a serialization shape, or
  which branch a task takes

It deliberately does **not** fire when the behaviour can simply be run and
observed: running is cheaper and exercises the real path. And it stops the
moment a version-matched sources jar (or the tagged source for that exact
version) exists: bytecode is the fallback, not the goal.

## Example

Claim: "the plugin's validator defaults to strict, so setting the threshold is
a no-op." What changes if false: the build is not enforcing what everyone
thinks it is.

```
find ~/.gradle/caches/modules-2/files-2.1 -path '*<artifact>*' -name '*.jar' | grep -v sources
unzip -o -q <jar> '<pkg>/<Class>*'
javap -p -c '<pkg>/<Class>.class'
```

Defaults live in `static {}` / `<clinit>`, as the constant pushed before the
constructor call; Kotlin default arguments hide in the `$default` synthetic
bridge, not the signature. The report quotes what was found, not a verdict:
`ThresholdValidator(0F)` at `<clinit>` is a fact someone else can check; "the
default is strict" is only an assertion.

Two traps the procedure guards on the way: decompile the version this build
actually resolves (`./gradlew :app:dependencies` settles it, not the newest jar
in the cache), and beware the no-op that reads like a tightening: setting an
option to its existing default advertises a guarantee nobody added.

## Related

- `prove-the-check-can-fail`, the complement: that skill asks whether your
  check would catch the bug, this one asks whether the library does what its
  name implies.
