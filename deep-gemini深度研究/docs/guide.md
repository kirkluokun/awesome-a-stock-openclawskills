The Gemini Deep Research Agent autonomously plans, executes, and synthesizes
multi-step research tasks. Powered by Gemini 3 Pro, it navigates complex
information landscapes using web search and your own data to produce detailed,
cited reports.

Research tasks involve iterative searching and reading and can take several
minutes to complete. You must use **background execution** (set `background=true`)
to run the agent asynchronously and poll for results. See [Handling long
running tasks](https://ai.google.dev/gemini-api/docs/deep-research#long-running-tasks) for more details.
| **Preview:** The Gemini Deep Research Agent is currently in preview. The Deep Research agent is exclusively available using the [Interactions
| API](https://ai.google.dev/gemini-api/docs/interactions). You cannot access it through `generate_content`.

The following example shows how to start a research task in the background
and poll for results.  

### Python

    import time
    from google import genai

    client = genai.Client()

    interaction = client.interactions.create(
        input="Research the history of Google TPUs.",
        agent='deep-research-pro-preview-12-2025',
        background=True
    )

    print(f"Research started: {interaction.id}")

    while True:
        interaction = client.interactions.get(interaction.id)
        if interaction.status == "completed":
            print(interaction.outputs[-1].text)
            break
        elif interaction.status == "failed":
            print(f"Research failed: {interaction.error}")
            break
        time.sleep(10)

### JavaScript

    import { GoogleGenAI } from '@google/genai';

    const client = new GoogleGenAI({});

    const interaction = await client.interactions.create({
        input: 'Research the history of Google TPUs.',
        agent: 'deep-research-pro-preview-12-2025',
        background: true
    });

    console.log(`Research started: ${interaction.id}`);

    while (true) {
        const result = await client.interactions.get(interaction.id);
        if (result.status === 'completed') {
            console.log(result.outputs[result.outputs.length - 1].text);
            break;
        } else if (result.status === 'failed') {
            console.log(`Research failed: ${result.error}`);
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 10000));
    }

### REST

    # 1. Start the research task
    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": "Research the history of Google TPUs.",
        "agent": "deep-research-pro-preview-12-2025",
        "background": true
    }'

    # 2. Poll for results (Replace INTERACTION_ID)
    # curl -X GET "https://generativelanguage.googleapis.com/v1beta/interactions/INTERACTION_ID" \
    # -H "x-goog-api-key: $GEMINI_API_KEY"

## Research with your own data

Deep Research has access to a variety of tools. By default, the agent has access
to information on the public internet using the `google_search` and `url_context`
tool. You don't need to specify these tools by default. However, if you
additionally want to give the agent access to your own data by using the [File
Search](https://ai.google.dev/gemini-api/docs/file-search) tool you will need to add it as shown in
the following example.
**Experimental:** Using Deep Research with `file_search` is still experimental.  

### Python

    import time
    from google import genai

    client = genai.Client()

    interaction = client.interactions.create(
        input="Compare our 2025 fiscal year report against current public web news.",
        agent="deep-research-pro-preview-12-2025",
        background=True,
        tools=[
            {
                "type": "file_search",
                "file_search_store_names": ['fileSearchStores/my-store-name']
            }
        ]
    )

### JavaScript

    const interaction = await client.interactions.create({
        input: 'Compare our 2025 fiscal year report against current public web news.',
        agent: 'deep-research-pro-preview-12-2025',
        background: true,
        tools: [
            { type: 'file_search', file_search_store_names: ['fileSearchStores/my-store-name'] },
        ]
    });

### REST

    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": "Compare our 2025 fiscal year report against current public web news.",
        "agent": "deep-research-pro-preview-12-2025",
        "background": true,
        "tools": [
            {"type": "file_search", "file_search_store_names": ["fileSearchStores/my-store-name"]},
        ]
    }'

## Steerability and formatting

You can steer the agent's output by providing specific formatting instructions
in your prompt. This allows you to structure reports into specific sections and
subsections, include data tables, or adjust tone for different audiences (e.g.,
"technical," "executive," "casual").

Define the desired output format explicitly in your input text.  

### Python

    prompt = """
    Research the competitive landscape of EV batteries.

    Format the output as a technical report with the following structure:
    1. Executive Summary
    2. Key Players (Must include a data table comparing capacity and chemistry)
    3. Supply Chain Risks
    """

    interaction = client.interactions.create(
        input=prompt,
        agent="deep-research-pro-preview-12-2025",
        background=True
    )

### JavaScript

    const prompt = `
    Research the competitive landscape of EV batteries.

    Format the output as a technical report with the following structure:
    1. Executive Summary
    2. Key Players (Must include a data table comparing capacity and chemistry)
    3. Supply Chain Risks
    `;

    const interaction = await client.interactions.create({
        input: prompt,
        agent: 'deep-research-pro-preview-12-2025',
        background: true,
    });

### REST

    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": "Research the competitive landscape of EV batteries.\n\nFormat the output as a technical report with the following structure: \n1. Executive Summary\n2. Key Players (Must include a data table comparing capacity and chemistry)\n3. Supply Chain Risks",
        "agent": "deep-research-pro-preview-12-2025",
        "background": true

## Multimodal inputs

Deep Research supports multimodal inputs, including images, PDFs, audio, and video,
allowing the agent to analyze rich content and then conduct web-based research
contextualized by the provided inputs. For example, you can provide a photograph
and ask the agent to identify subjects, research their behavior, or find related information.

The following example demonstrates an image analysis request using an
image URL.  

### Python

    import time
    from google import genai

    client = genai.Client()

    prompt = '''Analyze the interspecies dynamics and behavioral risks present
    in the provided image of the African watering hole. Specifically, investigate
    the symbiotic relationship between the avian species and the pachyderms
    shown, and conduct a risk assessment for the reticulated giraffes based on
    their drinking posture relative to the specific predator visible in the
    foreground.'''

    interaction = client.interactions.create(
        input=[
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "uri": "https://storage.googleapis.com/generativeai-downloads/images/generated_elephants_giraffes_zebras_sunset.jpg"
            }
        ],
        agent="deep-research-pro-preview-12-2025",
        background=True
    )

    print(f"Research started: {interaction.id}")

    while True:
        interaction = client.interactions.get(interaction.id)
        if interaction.status == "completed":
            print(interaction.outputs[-1].text)
            break
        elif interaction.status == "failed":
            print(f"Research failed: {interaction.error}")
            break
        time.sleep(10)

### JavaScript

    import { GoogleGenAI } from '@google/genai';

    const client = new GoogleGenAI({});

    const prompt = `Analyze the interspecies dynamics and behavioral risks present
    in the provided image of the African watering hole. Specifically, investigate
    the symbiotic relationship between the avian species and the pachyderms
    shown, and conduct a risk assessment for the reticulated giraffes based on
    their drinking posture relative to the specific predator visible in the
    foreground.`;

    const interaction = await client.interactions.create({
        input: [
            { type: 'text', text: prompt },
            {
                type: 'image',
                uri: 'https://storage.googleapis.com/generativeai-downloads/images/generated_elephants_giraffes_zebras_sunset.jpg'
            }
        ],
        agent: 'deep-research-pro-preview-12-2025',
        background: true
    });

    console.log(`Research started: ${interaction.id}`);

    while (true) {
        const result = await client.interactions.get(interaction.id);
        if (result.status === 'completed') {
            console.log(result.outputs[result.outputs.length - 1].text);
            break;
        } else if (result.status === 'failed') {
            console.log(`Research failed: ${result.error}`);
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 10000));
    }

### REST

    # 1. Start the research task with image input
    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": [
            {"type": "text", "text": "Analyze the interspecies dynamics and behavioral risks present in the provided image of the African watering hole. Specifically, investigate the symbiotic relationship between the avian species and the pachyderms shown, and conduct a risk assessment for the reticulated giraffes based on their drinking posture relative to the specific predator visible in the foreground."},
            {"type": "image", "uri": "https://storage.googleapis.com/generativeai-downloads/images/generated_elephants_giraffes_zebras_sunset.jpg"}
        ],
        "agent": "deep-research-pro-preview-12-2025",
        "background": true
    }'

    # 2. Poll for results (Replace INTERACTION_ID)
    # curl -X GET "https://generativelanguage.googleapis.com/v1beta/interactions/INTERACTION_ID" \
    # -H "x-goog-api-key: $GEMINI_API_KEY"

## Handling long-running tasks

Deep Research is a multi-step process involving planning, searching, reading,
and writing. This cycle typically exceeds the standard timeout limits of
synchronous API calls.

Agents are required to use `background=True`. The API returns a partial
`Interaction` object immediately. You can use the `id` property to retrieve an
interaction for polling. The interaction state will transition from
`in_progress` to `completed` or `failed`.

### Streaming

Deep Research supports streaming to receive real-time updates on the research
progress. You must set `stream=True` and `background=True`.
| **Note:** To receive intermediate reasoning steps (thoughts) and progress updates, you must enable **thinking summaries** in the `agent_config`. If this is not set to `"auto"`, the stream may only provide the final results without the real-time thought process.

The following example shows how to start a research task and process the stream.
Crucially, it demonstrates how to track the `interaction_id` from the
`interaction.start` event. You will need this ID to resume the stream if a
network interruption occurs. This code also introduces an `event_id` variable
which lets you resume from the specific point where you disconnected.  

### Python

    stream = client.interactions.create(
        input="Research the history of Google TPUs.",
        agent="deep-research-pro-preview-12-2025",
        background=True,
        stream=True,
        agent_config={
            "type": "deep-research",
            "thinking_summaries": "auto"
        }
    )

    interaction_id = None
    last_event_id = None

    for chunk in stream:
        if chunk.event_type == "interaction.start":
            interaction_id = chunk.interaction.id
            print(f"Interaction started: {interaction_id}")

        if chunk.event_id:
            last_event_id = chunk.event_id

        if chunk.event_type == "content.delta":
            if chunk.delta.type == "text":
                print(chunk.delta.text, end="", flush=True)
            elif chunk.delta.type == "thought_summary":
                print(f"Thought: {chunk.delta.content.text}", flush=True)

        elif chunk.event_type == "interaction.complete":
            print("\nResearch Complete")

### JavaScript

    const stream = await client.interactions.create({
        input: 'Research the history of Google TPUs.',
        agent: 'deep-research-pro-preview-12-2025',
        background: true,
        stream: true,
        agent_config: {
            type: 'deep-research',
            thinking_summaries: 'auto'
        }
    });

    let interactionId;
    let lastEventId;

    for await (const chunk of stream) {
        // 1. Capture Interaction ID
        if (chunk.event_type === 'interaction.start') {
            interactionId = chunk.interaction.id;
            console.log(`Interaction started: ${interactionId}`);
        }

        // 2. Track IDs for potential reconnection
        if (chunk.event_id) lastEventId = chunk.event_id;

        // 3. Handle Content
        if (chunk.event_type === 'content.delta') {
            if (chunk.delta.type === 'text') {
                process.stdout.write(chunk.delta.text);
            } else if (chunk.delta.type === 'thought_summary') {
                console.log(`Thought: ${chunk.delta.content.text}`);
            }
        } else if (chunk.event_type === 'interaction.complete') {
            console.log('\nResearch Complete');
        }
    }

### REST

    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": "Research the history of Google TPUs.",
        "agent": "deep-research-pro-preview-12-2025",
        "background": true,
        "stream": true,
        "agent_config": {
            "type": "deep-research",
            "thinking_summaries": "auto"
        }
    }'
    # Note: Look for the 'interaction.start' event to get the interaction ID.

### Reconnecting to stream

Network interruptions can occur during long-running research tasks. To handle
this gracefully, your application should catch connection errors and resume the
stream using `client.interactions.get()`.

You must provide two values to resume:

1. **Interaction ID:** Acquired from the `interaction.start` event in the initial stream.
2. **Last Event ID:** The ID of the last successfully processed event. This tells the server to resume sending events *after* that specific point. If not provided, you will get the beginning of the stream.

The following examples demonstrate a resilient pattern: attempting to stream the
initial `create` request, and falling back to a `get` loop if the connection
drops.  

### Python

    import time
    from google import genai

    client = genai.Client()

    # Configuration
    agent_name = 'deep-research-pro-preview-12-2025'
    prompt = 'Compare golang SDK test frameworks'

    # State tracking
    last_event_id = None
    interaction_id = None
    is_complete = False

    def process_stream(event_stream):
        """Helper to process events from any stream source."""
        global last_event_id, interaction_id, is_complete
        for event in event_stream:
            # Capture Interaction ID
            if event.event_type == "interaction.start":
                interaction_id = event.interaction.id
                print(f"Interaction started: {interaction_id}")

            # Capture Event ID
            if event.event_id:
                last_event_id = event.event_id

            # Print content
            if event.event_type == "content.delta":
                if event.delta.type == "text":
                    print(event.delta.text, end="", flush=True)
                elif event.delta.type == "thought_summary":
                    print(f"Thought: {event.delta.content.text}", flush=True)

            # Check completion
            if event.event_type in ['interaction.complete', 'error']:
                is_complete = True

    # 1. Attempt initial streaming request
    try:
        print("Starting Research...")
        initial_stream = client.interactions.create(
            input=prompt,
            agent=agent_name,
            background=True,
            stream=True,
            agent_config={
                "type": "deep-research",
                "thinking_summaries": "auto"
            }
        )
        process_stream(initial_stream)
    except Exception as e:
        print(f"\nInitial connection dropped: {e}")

    # 2. Reconnection Loop
    # If the code reaches here and is_complete is False, we resume using .get()
    while not is_complete and interaction_id:
        print(f"\nConnection lost. Resuming from event {last_event_id}...")
        time.sleep(2) 

        try:
            resume_stream = client.interactions.get(
                id=interaction_id,
                stream=True,
                last_event_id=last_event_id
            )
            process_stream(resume_stream)
        except Exception as e:
            print(f"Reconnection failed, retrying... ({e})")

### JavaScript

    let lastEventId;
    let interactionId;
    let isComplete = false;

    // Helper to handle the event logic
    const handleStream = async (stream) => {
        for await (const chunk of stream) {
            if (chunk.event_type === 'interaction.start') {
                interactionId = chunk.interaction.id;
            }
            if (chunk.event_id) lastEventId = chunk.event_id;

            if (chunk.event_type === 'content.delta') {
                if (chunk.delta.type === 'text') {
                    process.stdout.write(chunk.delta.text);
                } else if (chunk.delta.type === 'thought_summary') {
                    console.log(`Thought: ${chunk.delta.content.text}`);
                }
            } else if (chunk.event_type === 'interaction.complete') {
                isComplete = true;
            }
        }
    };

    // 1. Start the task with streaming
    try {
        const stream = await client.interactions.create({
            input: 'Compare golang SDK test frameworks',
            agent: 'deep-research-pro-preview-12-2025',
            background: true,
            stream: true,
            agent_config: {
                type: 'deep-research',
                thinking_summaries: 'auto'
            }
        });
        await handleStream(stream);
    } catch (e) {
        console.log('\nInitial stream interrupted.');
    }

    // 2. Reconnect Loop
    while (!isComplete && interactionId) {
        console.log(`\nReconnecting to interaction ${interactionId} from event ${lastEventId}...`);
        try {
            const stream = await client.interactions.get(interactionId, {
                stream: true,
                last_event_id: lastEventId
            });
            await handleStream(stream);
        } catch (e) {
            console.log('Reconnection failed, retrying in 2s...');
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

### REST

    # 1. Start the research task (Initial Stream)
    # Watch for event: interaction.start to get the INTERACTION_ID
    # Watch for "event_id" fields to get the LAST_EVENT_ID
    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": "Compare golang SDK test frameworks",
        "agent": "deep-research-pro-preview-12-2025",
        "background": true,
        "stream": true,
        "agent_config": {
            "type": "deep-research",
            "thinking_summaries": "auto"
        }
    }'

    # ... Connection interrupted ...

    # 2. Reconnect (Resume Stream)
    # Pass the INTERACTION_ID and the LAST_EVENT_ID you saved.
    curl -X GET "https://generativelanguage.googleapis.com/v1beta/interactions/INTERACTION_ID?stream=true&last_event_id=LAST_EVENT_ID&alt=sse" \
    -H "x-goog-api-key: $GEMINI_API_KEY"

## Follow-up questions and interactions

You can continue the conversation after the agent returns the final report by
using the `previous_interaction_id`. This lets you to ask for clarification,
summarization or elaboration on specific sections of the research without
restarting the entire task.  

### Python

    import time
    from google import genai

    client = genai.Client()

    interaction = client.interactions.create(
        input="Can you elaborate on the second point in the report?",
        model="gemini-3-pro-preview",
        previous_interaction_id="COMPLETED_INTERACTION_ID"
    )

    print(interaction.outputs[-1].text)

### JavaScript

    const interaction = await client.interactions.create({
        input: 'Can you elaborate on the second point in the report?',
        agent: 'deep-research-pro-preview-12-2025',
        previous_interaction_id: 'COMPLETED_INTERACTION_ID'
    });
    console.log(interaction.outputs[-1].text);

### REST

    curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
    -H "Content-Type: application/json" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -d '{
        "input": "Can you elaborate on the second point in the report?",
        "agent": "deep-research-pro-preview-12-2025",
        "previous_interaction_id": "COMPLETED_INTERACTION_ID"
    }'

## When to use Gemini Deep Research Agent

Deep Research is an **agent**, not just a model. It is best suited for workloads
that require an "analyst-in-a-box" approach rather than low-latency chat.

| Feature | Standard Gemini Models | Gemini Deep Research Agent |
|---|---|---|
| **Latency** | Seconds | Minutes (Async/Background) |
| **Process** | Generate -\> Output | Plan -\> Search -\> Read -\> Iterate -\> Output |
| **Output** | Conversational text, code, short summaries | Detailed reports, long-form analysis, comparative tables |
| **Best For** | Chatbots, extraction, creative writing | Market analysis, due diligence, literature reviews, competitive landscaping |

## Availability and pricing

You can access the Gemini Deep Research Agent using the Interactions API in Google AI Studio and the Gemini API.

Pricing follows a [pay-as-you-go model](https://ai.google.dev/gemini-api/docs/pricing#pricing-for-agents) based on the underlying [Gemini 3 Pro](https://ai.google.dev/gemini-api/docs/pricing#gemini-3-pro-preview) model and the specific tools the agent utilizes. Unlike standard chat requests, where a request leads to one output, a Deep Research task is an agentic workflow. A single request triggers an autonomous loop of planning, searching, reading, and reasoning.

### Estimated costs

Costs vary based on the depth of research required. The agent autonomously determines how much reading and searching is necessary to answer your prompt.

- **Standard research task:** For a typical query requiring moderate analysis, the agent might use \~80 search queries, \~250k input tokens (\~50-70% cached), and \~60k output tokens.
  - **Estimated total:** \~$2.00 -- $3.00 per task
- **Complex research task:** For deep competitive landscape analysis or extensive due diligence, the agent might use up to \~160 search queries, \~900k input tokens (\~50-70% cached), and \~80k output tokens.
  - **Estimated total:** \~$3.00 -- $5.00 per task

| **Note:** These figures are estimates based on preview rates and are subject to change.

## Safety considerations

Giving an agent access to the web and your private files requires careful
consideration of safety risks.

- **Prompt injection using files:** The agent reads the contents of the files you provide. Ensure that uploaded documents (PDFs, text files) come from trusted sources. A malicious file could contain hidden text designed to manipulate the agent's output.
- **Web content risks:** The agent searches the public web. While we implement robust safety filters, there is a risk that the agent may encounter and process malicious web pages. We recommend reviewing the `citations` provided in the response to verify the sources.
- **Exfiltration:** Be cautious when asking the agent to summarize sensitive internal data if you are also allowing it to browse the web.

## Best practices

- **Prompt for unknowns:** Instruct the agent on how to handle missing data. For example, add *"If specific figures for 2025 are not available,
  explicitly state they are projections or unavailable rather than
  estimating"* to your prompt.
- **Provide context:** Ground the agent's research by providing background information or constraints directly in the input prompt.
- **Multimodal inputs** Deep Research Agent supports multi-modal inputs. Use cautiously, as this increases costs and risks context window overflow.

## Limitations

- **Beta status**: The Interactions API is in public beta. Features and schemas may change.
- **Custom tools:** You cannot currently provide custom Function Calling tools or remote MCP (Model Context Protocol) servers to the Deep Research agent.
- **Structured output and plan approval:** The Deep Research Agent currently doesn't support human approved planning or structured outputs.
- **Max research time:** The Deep Research agent has a maximum research time of 60 minutes. Most tasks should complete within 20 minutes.
- **Store requirement:** Agent execution using `background=True` requires `store=True`.
- **Google search:** [Google
  Search](https://ai.google.dev/gemini-api/docs/google-search) is enabled by default and [specific
  restrictions](https://ai.google.dev/gemini-api/terms#use-restrictions2) apply to the grounded results.
- **Audio inputs:** Audio inputs are not supported.

## What's next

- Learn more about the [Interactions API](https://ai.google.dev/gemini-api/docs/interactions).
- Read about the [Gemini 3 Pro](https://ai.google.dev/gemini-api/docs/models/gemini-3) model that powers this agent.
- Learn how to use your own data using the [File Search](https://ai.google.dev/gemini-api/docs/file-search) tool.