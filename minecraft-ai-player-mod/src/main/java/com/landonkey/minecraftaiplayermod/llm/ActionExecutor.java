package com.landonkey.minecraftaiplayermod.llm;

import java.util.concurrent.atomic.AtomicBoolean;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.WalkAnimationState;

public class ActionExecutor {

    private static final Minecraft mc = Minecraft.getInstance();

    public static void movePlayer(String direction, double distance) {
        distance = Math.max(0.5, distance * 10);
        LocalPlayer player = mc.player;
        if (player == null) return;

        //player.jumpFromGround();

        // Calculate movement vector based on direction
        double dx = 0, dz = 0;
        switch (direction.toLowerCase()) {
            case "forward":
                dx = -Math.sin(Math.toRadians(player.getYRot()));
                dz = Math.cos(Math.toRadians(player.getYRot()));
                break;
            case "backward":
                dx = Math.sin(Math.toRadians(player.getYRot()));
                dz = -Math.cos(Math.toRadians(player.getYRot()));
                break;
            case "left":
                dx = -Math.cos(Math.toRadians(player.getYRot()));
                dz = -Math.sin(Math.toRadians(player.getYRot()));
                break;
            case "right":
                dx = Math.cos(Math.toRadians(player.getYRot()));
                dz = Math.sin(Math.toRadians(player.getYRot()));
                break;
            default:
                System.out.println("Unknown direction: {}" + direction + "} moving forward instead.");
                dx = -Math.sin(Math.toRadians(player.getYRot()));
                dz = Math.cos(Math.toRadians(player.getYRot()));
        }

        // Calculate new position
        double newX = player.getX() + dx * distance;
        double newZ = player.getZ() + dz * distance;
        double newY = player.getY() + 1;
        
        player.walkAnimation.setSpeed((float)distance);
        // Move player to new position
        player.moveTo(newX, newY, newZ);
        
    }
}
