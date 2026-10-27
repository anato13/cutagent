# Group-comedy Auto Edit preset

This optional preset responds to Anato12's request to use both a shared
VanossGaming Gmod Prop Hunt video and a finished video edited by Anato12's
friend. It is an **original editing approach**,
not a copy of the video's footage, graphics, sound effects, branding or jokes.
The reference file stays outside the app and the source package.

## What was actually inspected

The shared 25:36 MP4 was accessible locally for this milestone. Its embedded
English subtitle track contained 849 entries. Frames were sampled from the
opening 90 seconds, 10:00–11:30 and 23:20–24:50; caption excerpts from the
opening, 10:00–10:40 and 23:20–24:10 were reviewed. The opening
uses a playful premise before gameplay; later samples center on improvised
friend-group conversation, misunderstandings and reactions. Gameplay shots are
often allowed to continue while the conversation develops. These samples do not
establish a complete statistical account of the creator's editing style, and
subtitle text cannot reliably identify speakers or prove what viewers find funny.

## What the preset does

Choose **Group comedy (experimental)** in Auto Edit. The selection priority gives
modest preference to complete banter, misunderstandings, callbacks and awkward
exchanges, and to shorter complete ranges. Existing approved clips still take
priority. Studio remembers your approach selection on this computer. Finder may
make its validated second coverage pass until it has up to
four distinct candidates, if supported by the recording; four is not a quota.
The local model receives a separate group-comedy selection prompt, and cached
responses are keyed by approach so normal story analysis cannot reuse them.
The friend-edited example adds one rule: keep the first setup of a recurring bit
before a later callback. The preset gives model-labeled callbacks a modest
priority boost, but keeps a callback after earlier selected context instead of
automatically using it as a cold open. Model category labels still need review.
For group-comedy model requests, exact repeated topic words at least a minute
apart can supply earlier caption lines as source references. The same earlier
line consumes only one reference slot per analysis window. A shared word is
only a reason to show context to the model; it does not establish a joke or a
callback, and it does not create a clip on its own.
If at least three selected moments exist, a short later exchange with a cited
model reaction may move to the opening. The same footage is used only once, and
the other clips remain in source order. A source-linked story-playbook opening
takes precedence when both options are enabled. The manifest records the chosen
style, source reaction IDs, ordering reason and whether the proposal was applied.

The preset does **not** infer who said a line, validate a model's interpretation
of a reaction, detect visual faces or sound effects, insert copyrighted assets,
or train model weights. It never shortens a complete selected exchange merely
to meet a pace target. Every export still needs playback review for comedy and
story quality. A focused local-model check returned one structurally valid
candidate from 27 lines of an older Anato12 conversation; this does not prove
full-recording recall or editorial quality.

## Friend-edited Anato12 example

The shared finished MP4 is 10:26 and has 290 embedded subtitle entries. Sampled
frames from 0:00–1:30, 2:00–3:30, 5:00–6:30 and 8:30–10:20 show a brief spoken
opening, a title card around 0:04–0:10, speaker-labeled captions, occasional
face close-ups and restrained visual inserts. Its caption text returns to
earlier topics: one bit begins around 0:12 and reappears after 4:00 and 6:00;
another appears around 2:05 and returns near 5:00. These are transcript and
sampled-frame observations, not a measured viewer-engagement result. The older
raw gaming recording available here has different dialogue, so the original
footage for this finished edit was **not** available for a cut-by-cut comparison.

Studio can use the setup/callback preference in its local-model prompt and
group-comedy ordering. It cannot yet assign speakers reliably or place face
close-ups automatically, so it does not reproduce the friend's caption labels,
title card or reframing. This example is a preference reference, not training
of the model's weights.

In one live check of the updated prompt, `qwen2.5:7b` received 32 caption
lines from 4:20–5:35 with four earlier source references and returned zero
candidates. The reference delivery and test suite therefore verify context
plumbing, not reliable humor recognition on this edit.
