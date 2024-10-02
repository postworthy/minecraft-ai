package com.landonkey.minecraftaiplayermod.llm;

import java.util.List;
import org.yaml.snakeyaml.Yaml;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class Instruction {
    String action;
    Parameters parameters;

    public static Instruction fromYaml(String yaml) {
        // Create a new YAML parser instance
        Yaml parser = new Yaml();

        // Parse the YAML string into a Map
        Map<String, Object> yamlMap = parser.load(yaml);

        // Create a new Instruction object
        Instruction instruction = new Instruction();

        // Extract the "action" data from the YAML map
        if (yamlMap.containsKey("action")) {
            Map<String, Object> actionMap = (Map<String, Object>) yamlMap.get("action");

            // Set the function name to the action field
            if (actionMap.containsKey("function")) {
                instruction.action = (String) actionMap.get("function");
            }

            // Extract and populate the parameters
            if (actionMap.containsKey("parameters")) {
                Map<String, Object> parametersMap = (Map<String, Object>) actionMap.get("parameters");

                // Create a new Parameters object
                Parameters params = new Instruction().new Parameters();

                // Populate fields in Parameters based on expected keys
                params.distance = parametersMap.containsKey("distance") ? (Double) parametersMap.get("distance") : 0.0;
                params.direction = parametersMap.containsKey("direction") ? (String) parametersMap.get("direction") : "";

                // Add other fields as necessary, based on your YAML structure
                // For example, params.blockName = (String) parametersMap.getOrDefault("blockName", "");

                // Set the parameters in the instruction object
                instruction.parameters = params;
            }
        }

        return instruction;
    }

    class Parameters {
        // PlayerInteractEvent
        String blockName;
        String interactionType;
        String position;

        // AttackEntityEvent
        String entityType;
        String weaponName;

        // TickEvent.PlayerTickEvent
        String direction;
        double distance;

        // ItemCraftedEvent
        String itemName;
        int count;
        List<String> ingredients;

        // AnvilRepairEvent
        String leftItemName;
        String rightItemName;
        String resultItemName;

        // PlayerContainerEvent
        String containerName;


        // ArrowNockEvent
        String bowName;

        // ArrowLooseEvent

        int charge;
        float power;

        // BonemealEvent
        String targetBlockName;

        // PlayerSleepInBedEvent
        String bedPosition;

        // PlayerWakeUpEvent
        boolean wakeImmediately;
    }
}
