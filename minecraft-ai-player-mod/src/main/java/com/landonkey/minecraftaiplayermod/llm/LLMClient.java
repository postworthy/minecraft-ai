package com.landonkey.minecraftaiplayermod.llm;

import okhttp3.*;

import java.io.IOException;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import org.slf4j.Logger;

public class LLMClient {
    private static final OkHttpClient client = new OkHttpClient();
    private static final String LLM_ENDPOINT = "http://localhost:5555";
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public static void sendRequest(String prompt, Callback callback) {
        MediaType JSON = MediaType.parse("application/json; charset=utf-8");

        // Construct JSON payload
        JsonObject payload = new JsonObject();
        payload.addProperty("model", "minecraft-ai");
        payload.addProperty("stream", false);
        payload.addProperty("prompt", prompt);

        String jsonPayload = GSON.toJson(payload);

        LOGGER.info("Sending request with payload: {}", jsonPayload);
        RequestBody body = RequestBody.create(jsonPayload, JSON);
        Request request = new Request.Builder()
                .url(LLM_ENDPOINT + "/api/generate")
                .post(body)
                .build();

        client.newCall(request).enqueue(callback);
    }

    public static void listAvailableModels(Callback callback) {
        Request request = new Request.Builder()
                .url(LLM_ENDPOINT + "/api/tags") // Append /api/tags path to LLM_ENDPOINT
                .get() // Use GET request
                .build();

        client.newCall(request).enqueue(callback);
    }
}
