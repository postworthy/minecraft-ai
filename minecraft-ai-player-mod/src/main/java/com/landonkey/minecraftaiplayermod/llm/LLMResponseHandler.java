package com.landonkey.minecraftaiplayermod.llm;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.Response;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;

import org.slf4j.Logger;

import com.google.gson.JsonSyntaxException;
import com.landonkey.minecraftaiplayermod.event.PlayerEventHandler;
import com.mojang.logging.LogUtils;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.GsonBuilder;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class LLMResponseHandler {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static AtomicBoolean idle = new AtomicBoolean(true);

    public static synchronized void setIdleState(boolean idleState) {
        LLMResponseHandler.idle.set(idleState);
    }

    public static synchronized boolean getIdleState() {
        return LLMResponseHandler.idle.get();
    }

    public static void handleResponse(String jsonResponse) {
        try {
            JsonObject responseObject = GSON.fromJson(jsonResponse, JsonObject.class);
            if (responseObject.has("response")) {
                String fullResponse = responseObject.get("response").getAsString();

                // Define regex patterns to extract content between ```yml or ```yaml
                String yamlPattern = "```(?:yml|yaml)([\\s\\S]*?)```";
                Pattern pattern = Pattern.compile(yamlPattern);
                Matcher matcher = pattern.matcher(fullResponse);

                if (matcher.find()) {
                    String yamlResponse = matcher.group(1).trim(); // Get the captured group (YAML content)
                    LOGGER.info("Extracted YAML response:\n" + yamlResponse);

                    PlayerEventHandler.PREVIOUS_PROMPT = PlayerEventHandler.PREVIOUS_PROMPT + yamlResponse + "\n\n";

                    Instruction instruction = Instruction.fromYaml(yamlResponse);
                    switch (instruction.action) {
                        case "move":
                            ActionExecutor.movePlayer(instruction.parameters.direction,
                                    instruction.parameters.distance);
                            break;
                        // Add more cases if needed
                    }
                } else {
                    throw new IllegalArgumentException("No valid YAML block found in the response.");
                }
            }
        } catch (Exception ex) {
            LOGGER.error("Error handling response: " + ex.toString());
        }
    }

    public static void requestAndHandle(String prompt) {
        if (LLMResponseHandler.getIdleState()) {
            LLMResponseHandler.setIdleState(false);

            LLMClient.sendRequest(prompt, new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    LOGGER.error(e.toString());
                    LLMResponseHandler.setIdleState(true);
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (!response.isSuccessful()) {
                        // LOGGER.error("Unexpected code " + response);
                        LLMResponseHandler.setIdleState(true);
                        return;
                    }

                    String responseBody = response.body().string();
                    // LOGGER.info("LLM Response: " + responseBody);
                    handleResponse(responseBody);
                    LLMResponseHandler.setIdleState(true);
                }
            });
        }
    }
}
