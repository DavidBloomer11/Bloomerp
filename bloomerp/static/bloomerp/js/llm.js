
async function llmContentStreamer(
    url, // URL endpoint
    id, // Base ID of the content element
    queryType, // Query type for the llm
    targetElement,
    args // Are a string value of arguments with the format arg1=value1;arg2=value2
) {
    // Get csrf token from the cookie
    const csrfToken = getCookie("csrftoken");
    
    // Format the arguments
    var argsArray = args.split(";");
    var argsObject = {};
    argsArray.forEach((arg) => {
        var argArray = arg.split("=");
        argsObject[argArray[0]] = argArray[1];
    });

    // First get the conversation element using the id
    var conversationContainer = document.getElementById(`conversation_container_${id}`);

    // Get both the user and assistance messages
    var userMessages = conversationContainer.querySelectorAll(".user-bubble");
    var assistanceMessages = conversationContainer.querySelectorAll(".assistant-bubble");

    // Prepare the conversation history
    var conversation_history = [];

    // Now return the conversation history with user message first, assistance message, user message, assistance message, and so on
    let userIndex = 0;
    let assistanceIndex = 0;

    while (userIndex < userMessages.length || assistanceIndex < assistanceMessages.length) {
        if (userIndex < userMessages.length) {
            conversation_history.push({
                content: userMessages[userIndex].innerText,
                role: "user",
            });
            userIndex++;
        }
        if (assistanceIndex < assistanceMessages.length) {
            conversation_history.push({
                content: assistanceMessages[assistanceIndex].innerText,
                role: "assistant",
            });
            assistanceIndex++;
        }
    }


    // Get the input element
    var query = document.getElementById(`llm_query_${id}`).value;

    // If the query is empty, return
    if (query === "") {
        return;
    }

    // Create the user message
    // Generate a random id for the user message
    var userMessageId = `user_message_${Math.floor(Math.random() * 1000000)}`;
    var userMessage = bloomAiCreateMessage(query, true, userMessageId, id, queryType);

    // Append the user message to the conversation
    conversationContainer.appendChild(userMessage);

    // Create the assistance message
    // Generate a random id for the assistance message
    var assistanceMessageId = `assistance_message_${Math.floor(Math.random() * 1000000)}`;
    var assistanceMessage = bloomAiCreateMessage("", false, assistanceMessageId, id, queryType);

    // Append the assistance message to the conversation
    conversationContainer.appendChild(assistanceMessage);

    // Scroll to the bottom of the conversation
    conversationContainer.scrollTop = conversationContainer.scrollHeight;

    // Remove input value
    document.getElementById(`llm_query_${id}`).value = "";

    // Fetch the response from the server
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            query: query,
            query_type: queryType,
            conversation_history: conversation_history,
            args: argsObject,
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let result = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value, { stream: true });

        // Remove the ```html or ``` from the result, only when not bloom_ai
        if (queryType != 'bloom_ai') {
            result = result.replace("```html", "");
            result = result.replace("```", "");

            document.getElementById(assistanceMessageId).innerHTML = result;
        } else {
            // Markdown to HTML
            document.getElementById("md-"+assistanceMessageId).innerHTML = result;
        }

    }

}

function bloomAiCreateMessage(message, isUser, bubbleId, baseElementId, queryType) {
    var messageContainer = document.createElement("div");
    messageContainer.className = "ai-message-container mb-2";

    // Wrapper
    var wrapper = document.createElement("div");
    wrapper.className = isUser ? "d-flex justify-content-end" : "d-flex justify-content-start";

    // Create bubble
    var messageBubble = document.createElement("div");
    messageBubble.id = bubbleId;

    messageBubble.className = isUser ? "user-bubble" : "assistant-bubble";

    // If the message is from the user, add the content
    if (isUser) {
        messageBubble.innerHTML = message;
    } else {
        // Add the spinner
        var spinner = createSpinner(false);
        messageBubble.appendChild(spinner);
    }

    // Append the message bubble to the wrapper
    wrapper.appendChild(messageBubble);
    messageContainer.appendChild(wrapper);

    // Add another div
    var utilsDiv = document.createElement("div");
    utilsDiv.className = isUser ? "d-flex justify-content-end mb-3 gap-2" : "d-flex justify-content-start mb-3 gap-2";

    // Add copy button
    var copyButton = document.createElement("a");
    copyButton.className = "bi bi-clipboard pointer";
    copyButton.title = "Copy to clipboard";
    copyButton.onclick = function () {
        navigator.clipboard.writeText(document.getElementById(bubbleId).innerText);
    }

    // Add insert to target button
    var insertButton = document.createElement("a");
    insertButton.className = "bi bi-arrow-down-circle pointer";
    insertButton.title = "Insert to target";
    var target = document.getElementById(`llm_output_${baseElementId}`);

    // Add the onclick event
    insertButton.onclick = function () {
        target.innerHTML = document.getElementById(bubbleId).innerHTML;
        target.dispatchEvent(new Event('llm-inserted'));
    }
    
    // Add data-bs-dismiss attribute
    insertButton.setAttribute("data-bs-dismiss", "modal");

    if (queryType == 'bloom_ai') {
        // Add zero-md to the utils div
        let zeroMd = document.createElement("zero-md");
        let script = document.createElement("script");
        script.type = "text/markdown";
        script.id = "md-" + bubbleId;
        zeroMd.appendChild(script);

        if (!isUser) {
            // Add the markdown content to the script
            messageBubble.appendChild(zeroMd);
        }

        // Append the zero-md to the bubble
        messageBubble.appendChild(zeroMd);
    }

    // Append the copy button to the utils div
    if (queryType != 'bloom_ai') {
    utilsDiv.appendChild(insertButton);
    }
    utilsDiv.appendChild(copyButton);

    // Append the utils div to the message container
    messageContainer.appendChild(utilsDiv);

    return messageContainer;
}


