package com.landonkey.minecraftaiplayermod.event;

import java.io.StringWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;

import com.landonkey.minecraftaiplayermod.MinecraftAiPlayerMod;
import com.landonkey.minecraftaiplayermod.llm.LLMResponseHandler;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = MinecraftAiPlayerMod.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public class PlayerEventHandler {
    private static final Map<UUID, Vec3> playerPositions = new HashMap<>();
    private static final Map<UUID, Integer> playerTickCounters = new HashMap<>();
    private static final int TICKS_PER_SECOND = 20;
    private static final String PRE = "Act as an expert Minecraft player who can understand a player's actions by viewing the game state at the time the action was given. I will provide you with the game state and the action taken in YAML form, and you will tell me why a player may have taken the given action using your knowledge of Minecraft and the game state, be highly detailed and provide your reasoning step by step for the sample data below. Always include in your respons a yml block with your next predicted action.\n\n";
    
    public static String PREVIOUS_PROMPT = "";

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END)
            return;

        Player player = event.player;
        UUID playerUUID = player.getUUID();
        Vec3 currentPos = player.getPosition(0);

        int tickCount = playerTickCounters.getOrDefault(playerUUID, 0) + 1;

        Vec3 prevPos = playerPositions.get(playerUUID);

        if (prevPos == null || !currentPos.equals(prevPos) || tickCount >= TICKS_PER_SECOND) {
            playerTickCounters.put(playerUUID, 0);

            // Collect common data
            Map<String, Object> data = collectCommonData(player, player.level(), player.getOnPos().above());

            // Update the stored previous position
            playerPositions.put(playerUUID, currentPos);

            // Write data to prompt
            String newPrompt = writeDataToPrompt(data);
            String prompt = PRE + PREVIOUS_PROMPT + newPrompt;
            PREVIOUS_PROMPT = newPrompt;

            LLMResponseHandler.requestAndHandle(prompt);
        }
        else {
            playerTickCounters.put(playerUUID, tickCount);
        }
    }

    private static String getMovementDirection(double dx, double dz, float yaw) {
        double movementAngle = Math.toDegrees(Math.atan2(dz, dx));
        double playerAngle = (yaw - 90) % 360;

        double angleDifference = (movementAngle - playerAngle + 360) % 360;

        if (angleDifference < 45 || angleDifference > 315) {
            return "forward";
        } else if (angleDifference >= 45 && angleDifference < 135) {
            return "left";
        } else if (angleDifference >= 135 && angleDifference < 225) {
            return "backward";
        } else {
            return "right";
        }
    }

    private static Map<String, Object> collectCommonData(Player player, Level level, BlockPos playerPos) {
        Map<String, Object> data = new LinkedHashMap<>();

        // Environment Information
        data.put("environment", collectEnvironmentData(level, playerPos));

        // Player State
        data.put("player", collectPlayerState(player));

        // Nearby Entities
        data.put("nearby_entities", collectNearbyEntities(player, level));

        // Map Blocks
        data.put("map_blocks", collectMapBlocks(level, playerPos));

        return data;
    }

    private static Map<String, Object> collectEnvironmentData(Level level, BlockPos playerPos) {
        Map<String, Object> environment = new HashMap<>();
        environment.put("time_of_day", level.isDay() ? "day" : "night");
        environment.put("weather", level.isRaining() ? "rain" : "clear");
        environment.put("biome", level.getBiome(playerPos).getRegisteredName());
        return environment;
    }

    private static Map<String, Object> collectPlayerState(Player player) {
        Map<String, Object> playerState = new HashMap<>();

        playerState.put("position",
                String.format("x=%.2f, y=%.2f, z=%.2f", player.getX(), player.getY(), player.getZ()));
        playerState.put("orientation", String.format("x=%.2f, y=%.2f, z=%.2f", player.getLookAngle().x,
                player.getLookAngle().y, player.getLookAngle().z));
        playerState.put("health", player.getHealth());
        playerState.put("hunger", player.getFoodData().getFoodLevel());

        // Inventory
        List<String> inventory = new ArrayList<>();
        player.getInventory().items.forEach(stack -> {
            if (!stack.isEmpty()) {
                int i = player.getInventory().items.indexOf(stack);
                inventory.add(String.format("Slot %d: %s x%d", i, stack.getDescriptionId(), stack.getCount()));
            }
        });
        playerState.put("inventory", inventory);

        return playerState;
    }

    private static List<Map<String, Object>> collectNearbyEntities(Player player, Level level) {
        List<Map<String, Object>> nearbyEntities = new ArrayList<>();
        BlockPos playerPos = player.blockPosition();

        // Define the area around the player to search for entities
        AABB searchArea = player.getBoundingBox().inflate(10);

        // Retrieve entities within the search area excluding the player
        List<Entity> entities = level.getEntities(player, searchArea, entity -> entity != player);

        for (Entity entity : entities) {
            Map<String, Object> entityData = new HashMap<>();
            String entityName = entity.getName().toString();

            // Calculate relative positions
            int dx = entity.blockPosition().getX() - playerPos.getX();
            int dy = entity.blockPosition().getY() - playerPos.getY();
            int dz = entity.blockPosition().getZ() - playerPos.getZ();

            entityData.put("type", entityName);
            entityData.put("position", String.format("dx=%d, dy=%d, dz=%d", dx, dy, dz));
            nearbyEntities.add(entityData);
        }

        return nearbyEntities;
    }

    private static List<String> collectMapBlocks(Level level, BlockPos playerPos) {
        List<String> mapBlocks = new ArrayList<>();

        // Cardinal directions
        mapBlocks.add(String.format("%s north of player",
                level.getBlockState(playerPos.north()).getBlock().getDescriptionId()));
        mapBlocks.add(String.format("%s south of player",
                level.getBlockState(playerPos.south()).getBlock().getDescriptionId()));
        mapBlocks.add(String.format("%s east of player",
                level.getBlockState(playerPos.east()).getBlock().getDescriptionId()));
        mapBlocks.add(String.format("%s west of player",
                level.getBlockState(playerPos.west()).getBlock().getDescriptionId()));

        // Intercardinal directions (diagonals)
        mapBlocks.add(String.format("%s northeast of player",
                level.getBlockState(playerPos.north().east()).getBlock().getDescriptionId()));
        mapBlocks.add(String.format("%s southeast of player",
                level.getBlockState(playerPos.south().east()).getBlock().getDescriptionId()));
        mapBlocks.add(String.format("%s southwest of player",
                level.getBlockState(playerPos.south().west()).getBlock().getDescriptionId()));
        mapBlocks.add(String.format("%s northwest of player",
                level.getBlockState(playerPos.north().west()).getBlock().getDescriptionId()));

        return mapBlocks;
    }

    public static String writeDataToPrompt(Map<String, Object> data) {
        // Set up DumperOptions for YAML formatting
        DumperOptions options = new DumperOptions();
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        options.setPrettyFlow(true);
        options.setIndent(2);

        // Create Yaml instance with custom options
        Yaml yaml = new Yaml(options);

        // Use StringWriter to capture YAML output as a string
        StringWriter stringWriter = new StringWriter();
        yaml.dump(data, stringWriter);

        // Return the YAML string
        return stringWriter.toString();
    }


}
