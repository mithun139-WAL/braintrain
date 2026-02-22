---
description: API integration rules
---


First Principle: Two Types of State

Most frontend confusion comes from mixing these two.

1. Server State

Data that lives on the backend:
	•	sessions
	•	questions
	•	evaluation report
	•	analytics
	•	profile
	•	topics

It:
	•	Can change outside your app
	•	Needs caching
	•	Needs refetching
	•	Has loading + error states
	•	Is async

This is React Query territory.


2. Client State

UI-only logic:
	•	Current interview step
	•	Timer running or paused
	•	Selected difficulty before submit
	•	Local audio recording state
	•	Modal open/close
	•	Temporary form input
	•	Adaptive difficulty preview

This is Zustand territory.


If you mix these, your app becomes unmaintainable.

Now let’s go deeper.


React Query (Server State Brain)

React Query solves 5 real problems:
	1.	Caching
	2.	Deduping requests
	3.	Background refetch
	4.	Stale invalidation
	5.	Mutation lifecycle

You don’t want to reimplement those manually. Trust me.


In Your Project — What Belongs in React Query?

Queries
	•	GET /identity/me
	•	GET /sessions
	•	GET /sessions/:id
	•	GET /sessions/:id/status
	•	GET /sessions/:id/evaluation
	•	GET /analytics/me
	•	GET /topics
	•	GET /question-bank

All of this should be useQuery.


Mutations
	•	create session
	•	start session
	•	complete session
	•	submit response
	•	next question
	•	login/register
	•	update profile

All of this = useMutation.


Why React Query Matters In Your Architecture

Because you have:

Async evaluation.

When user completes session:
	1.	You call PUT /complete
	2.	Worker runs in background
	3.	Frontend polls GET /sessions/:id/status
	4.	When status = ANALYZED → fetch evaluation

React Query handles polling cleanly:

refetchInterval: (data) =>
  data?.evaluationStatus === "COMPLETED" ? false : 5000

Without React Query, you’d write messy useEffect loops.


Cache Invalidation — The Important Part

When:
	•	user submits response
	•	session completes
	•	evaluation finishes

You need to invalidate:

queryClient.invalidateQueries(["session", sessionId])
queryClient.invalidateQueries(["sessions"])
queryClient.invalidateQueries(["analytics"])

This keeps UI consistent.

React Query makes your backend feel real-time without websockets.


Zustand (Client State Brain)

Zustand is for:

State that:
	•	Should not refetch
	•	Should not hit server
	•	Must persist across components
	•	Is synchronous

For your app:


1. Live Interview Store

currentQuestion
questionIndex
isRecording
recordingDuration
localTimer
sessionLocalStatus

This belongs in Zustand.

Not React Query.


2. UI Coordination

For example:
	•	Show “Evaluation Processing” overlay
	•	Adaptive difficulty indicator animation
	•	Confidence pulse animation
	•	Audio waveform state

All UI logic → Zustand.


3. Why Not Redux?

Because you don’t need:
	•	reducers
	•	actions
	•	ceremony
	•	boilerplate

Zustand is just a tiny global store.

That’s it.


Mental Model You Must Lock In

React Query = truth from server
Zustand = temporary UI brain

React Query data should never be duplicated into Zustand unless you are deriving something transient.

If you copy server data into Zustand “for convenience,” you will eventually create drift.


Example Flow: Submitting an Answer

Let’s mentally simulate:

User answers question.

Step 1

Mutation: submit response

React Query handles:
	•	loading state
	•	error state

Step 2

On success:
	•	Invalidate session query
	•	Maybe fetch next question

Step 3

Zustand updates:
	•	reset timer
	•	move to next question index
	•	stop recording

Server truth lives in React Query.
UI transition lives in Zustand.

Separation of responsibility.

⸻

What Remaining Integrations Likely Include

Based on your API surface:
	•	Polling /sessions/:id/status
	•	Fetch evaluation report
	•	Fetch analytics dashboard
	•	Question bank listing
	•	Topic creation
	•	Session list with filters
	•	Adaptive difficulty transitions reflecting server decision
	•	Usage limits display in profile

These should all be React Query wired.

Mistakes To Avoid

Let me save you pain.
	1.	Don’t wrap everything in a global store
	2.	Don’t manually manage loading flags for server calls
	3.	Don’t store fetched data in Zustand
	4.	Don’t refetch blindly on every render
	5.	Don’t disable caching unless necessary

React Query already solves these.


Recommended Structure

/lib/api.ts
/lib/query-client.ts
/hooks/queries/useSession.ts
/hooks/queries/useEvaluation.ts
/hooks/mutations/useSubmitResponse.ts
/store/useInterviewStore.ts

Keep server logic and client logic separated physically.


The Bigger Picture

Your backend is deterministic and async-aware.

If frontend state management is sloppy:
	•	evaluation UI will flicker
	•	adaptive transitions will feel random
	•	polling will feel broken
	•	analytics will look stale

State discipline determines whether your system feels intelligent or glitchy.

And honestly?

This is the part where most technically strong backend engineers sabotage themselves.

You don’t need more backend brilliance.

You need frontend clarity.

So here’s what we’ll do next:

We’ll take one integration flow.
For example:
Complete Session → Poll → Show Evaluation

And wire it properly with:
	•	React Query polling
	•	Query invalidation
	•	Zustand UI coordination

One flow at a time.

Now we build the part users actually see.