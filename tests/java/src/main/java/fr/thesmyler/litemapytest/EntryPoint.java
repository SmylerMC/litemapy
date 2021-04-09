import fi.dy.masa.litematica.schematic.container.LitematicaBitArray;
import py4j.GatewayServer;

public class EntryPoint {

    public static void main(String[] args) {
        GatewayServer gatewayServer = new GatewayServer(new EntryPoint());
        gatewayServer.start();
        System.out.println("[JAVA] Gateway Server Started...");
    }

}
