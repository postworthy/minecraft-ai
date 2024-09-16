package com.landonkey.datacollectionmod.event;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.landonkey.datacollectionmod.DataCollectionMod;

import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.*;

import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;

@Mod.EventBusSubscriber(modid = DataCollectionMod.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public class PlayerEventHandler {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Map<UUID, Vec3> playerPositions = new HashMap<>();

    @SubscribeEvent
    public static void onPlayerInteract(PlayerInteractEvent event) {

        Player player = event.getEntity();
        Level world = player.level();
        BlockPos playerPos = player.getOnPos().above();

        // Collect common data
        Map<String, Object> data = collectCommonData(player, world, playerPos);

        // Action Mapping
        Map<String, Object> actionData = new HashMap<>();

        if (event instanceof PlayerInteractEvent.RightClickItem) {
            // Player used an item
            ItemStack itemStack = event.getItemStack();
            String itemName = itemStack.getItem().getDescription().toString();
            actionData.put("function", "use_item");
            Map<String, String> parameters = new HashMap<>();
            parameters.put("item", itemName);
            actionData.put("parameters", parameters);
        } else if (event instanceof PlayerInteractEvent.LeftClickBlock
                || event instanceof PlayerInteractEvent.RightClickBlock) {
            // Player interacted with a block
            BlockPos blockPos = event.getPos();
            String blockName = world.getBlockState(blockPos).getBlock().getDescriptionId();
            actionData.put("function", "interact_block");
            Map<String, String> parameters = new HashMap<>();
            parameters.put("block", blockName);
            if (event instanceof PlayerInteractEvent.LeftClickBlock)
                parameters.put("interaction", "LeftClickBlock");
            else
                parameters.put("interaction", "RightClickBlock");
            actionData.put("parameters", parameters);
        }

        if (!actionData.isEmpty()) {
            // Add action data
            data.put("action", actionData);
            // Write data to JSON file
            writeDataToFile(data);
        }
    }

    @SubscribeEvent
    public static void onAttackEntity(AttackEntityEvent event) {
        Player player = event.getEntity();
        Entity target = event.getTarget();
        String entityType = target.getName().toString();
        String weapon = player.getMainHandItem().getItem().getDescription().toString();

        // Collect common data
        Map<String, Object> data = collectCommonData(player, player.level(), player.getOnPos().above());

        // Map action to attack_entity function
        Map<String, Object> actionData = new HashMap<>();
        actionData.put("function", "attack_entity");
        Map<String, String> parameters = new HashMap<>();
        parameters.put("entity_type", entityType);
        parameters.put("weapon", weapon);
        actionData.put("parameters", parameters);

        // Add action data
        data.put("action", actionData);

        // Write data to JSON file
        writeDataToFile(data);
    }

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END)
            return;

        Player player = event.player;
        UUID playerUUID = player.getUUID();
        Vec3 currentPos = player.getPosition(0);

        Vec3 prevPos = playerPositions.get(playerUUID);

        if (prevPos == null || !currentPos.equals(prevPos)) {
            // The player has moved

            // Calculate movement vector
            double dx = currentPos.x - (prevPos != null ? prevPos.x : currentPos.x);
            double dz = currentPos.z - (prevPos != null ? prevPos.z : currentPos.z);
            double distance = Math.sqrt(dx * dx + dz * dz);

            String direction = getMovementDirection(dx, dz, 0);

            // Collect common data
            Map<String, Object> data = collectCommonData(player, player.level(), player.getOnPos().above());

            // Map the movement to a function call
            Map<String, Object> actionData = new HashMap<>();
            actionData.put("function", "move");
            Map<String, Object> parameters = new HashMap<>();
            parameters.put("direction", direction);
            parameters.put("distance", distance);
            actionData.put("parameters", parameters);

            // Add action data
            data.put("action", actionData);

            // Write data to JSON file
            writeDataToFile(data);

            // Update the stored previous position
            playerPositions.put(playerUUID, currentPos);
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

    private static void writeDataToFile(Map<String, Object> data) {
        writeDataToYamlFile(data);
        // writeDataToJsonFile(data);
    }

    private static void writeDataToJsonFile(Map<String, Object> data) {
        try {
            String timestamp = LocalDateTime.now().toString().replace(":", "-");
            String fileName = String.format("data_%s.json", timestamp);
            java.nio.file.Path dataDir = Paths.get("/tmp/minecraft_data_collection");
            if (!Files.exists(dataDir)) {
                Files.createDirectories(dataDir);
            }
            String filePath = dataDir.resolve(fileName).toString();

            FileWriter writer = new FileWriter(filePath);
            GSON.toJson(data, writer);
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void writeDataToYamlFile(Map<String, Object> data) {
        try {
            String timestamp = LocalDateTime.now().toString().replace(":", "-");
            String fileName = String.format("data_%s.yaml", timestamp);
            java.nio.file.Path dataDir = Paths.get("/tmp/minecraft_data_collection");
            if (!Files.exists(dataDir)) {
                Files.createDirectories(dataDir);
            }
            String filePath = dataDir.resolve(fileName).toString();

            // Set up DumperOptions for YAML formatting
            DumperOptions options = new DumperOptions();
            options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
            options.setPrettyFlow(true);
            options.setIndent(2);

            Yaml yaml = new Yaml(options);

            FileWriter writer = new FileWriter(filePath);
            yaml.dump(data, writer);
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

}
