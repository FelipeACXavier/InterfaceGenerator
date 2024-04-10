package dtig;

import java.net.*;
import java.nio.ByteBuffer;
import java.io.*;
import java.lang.reflect.Array;

import dtig.*;

import com.mathworks.jmi.Matlab;

import com.google.protobuf.*;

public class ServerThread extends Thread
{
  enum State {
    UNINITIALIZED,
    INITIALIZING,
    IDLE,
    RUNNING,
    STEPPING,
    STOPPED
  }

  //initialize socket and input stream
  private Socket           socket  = null;
  private ServerSocket     server  = null;
  private DataInputStream  in      = null;
  private OutputStream     out     = null;
  // private Matlab           matlab  = null;
  private State            state   = State.UNINITIALIZED;


  public ServerThread(String host, int port)
  {
    // starts server and waits for a connection
    try
    {
      // this.matlab = new Matlab();
      this.server = new ServerSocket(port);
      System.out.println("Server started");
    }
    catch (IOException i)
    {
      System.out.println(i);
    }
  }

  public void runServer()
  {
    // starts server and waits for a connection
    try
    {
      System.out.println("Waiting for a client ...");

      socket = server.accept();
      System.out.println("Client accepted");

      // takes input from the client socket
      in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
      out = socket.getOutputStream();

      byte[] bytes = new byte[1024];

      // Read messages from the client until the client disconnects
      int count;
      while ((count = in.read(bytes)) > 0) {
        dtig.MDTMessage message = dtig.MDTMessage.parseFrom(ByteBuffer.wrap(bytes, 0, count));

        if (message.hasStop())
        {
          System.out.println("Stop message");
          Object[] args = {"STOPPED"};
          Matlab.mtFeval("setState", args, 0);
        }
        else if (message.hasStart())
          System.out.println("Start message");
        else if (message.hasSetInput())
          System.out.println("Set input message");
        else if (message.hasGetOutput())
          System.out.println("Get output message");
        else if (message.hasAdvance())
          System.out.println("Advance message");
        else if (message.hasInitialize())
        {
          System.out.println("Initialize message");
          Object[] args = {"INITIALIZED"};
          Matlab.mtFeval("setState", args, 0);
        }
        else if (message.hasSetParameter())
          System.out.println("Set parameter message");
        else if (message.hasGetParameter())
          System.out.println("Get parameter message");
        else
          System.out.println("Get model info");

        dtig.MReturnValue.Builder returnValue = dtig.MReturnValue.newBuilder()
          .setCode(dtig.EReturnCode.SUCCESS);

        out.write(returnValue.build().toByteArray());
      }

      System.out.println("Closing connection");

      // close connection
      socket.close();
      in.close();
    }
    catch(Exception e)
    {
      e.printStackTrace();
    }
  }

  @Override
  public void run()
  {
    this.runServer();
  }
}