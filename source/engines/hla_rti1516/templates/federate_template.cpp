// @imports
#include <RTI/LogicalTimeInterval.h>
#include <RTI/RTI1516fedTime.h>
#include <RTI/RTIambassador.h>
#include <RTI/RTIambassadorFactory.h>

#include <locale>
#include <codecvt>
#include <memory>

#include <string.h>

#include "// @>ambassador_header"

#include "dtig/dt_message.pb.h"
#include "dtig/initialize.pb.h"
#include "dtig/return_code.pb.h"
#include "dtig/advance.pb.h"
#include "dtig/start.pb.h"
#include "dtig/stop.pb.h"
#include "dtig/output.pb.h"
#include "dtig/parameter.pb.h"

#define MSG_SIZE 1024
#define PORT 8080
#define HOST "127.0.0.1"

using namespace std;
using namespace rti1516;

static const double STEP = 0.01;

// @classname
HLAFederate

// @constructor(public)
HLAFederate()
{
}

// @destructor(public)
~HLAFederate()
{
  if (mClient >= 0)
    close(mClient);
}

// @method(private)
std::wstring convertStringToWstring(const std::string& str)
{
  const std::ctype<wchar_t>& CType = std::use_facet<std::ctype<wchar_t> >(std::locale());
  std::vector<wchar_t> wideStringBuffer(str.length());
  CType.widen(str.data(), str.data() + str.length(), &wideStringBuffer[0]);
  return std::wstring(&wideStringBuffer[0], wideStringBuffer.size());
}

// @run
void runFederate(std::string federateName, std::string fom, std::string address, uint32_t port)
{
  rti1516::RTIambassadorFactory* factory = new rti1516::RTIambassadorFactory();
  std::vector<std::wstring> args;
  args.push_back(L"protocol=rti");
  args.push_back(L"address=" + convertStringToWstring(address));

  rtiamb = factory->createRTIambassador(args);

  try
  {
    rtiamb->createFederationExecution(L"ExampleFederation", convertStringToWstring(fom));
    std::cout << "Created Federation" << std::endl;
  }
  catch (FederationExecutionAlreadyExists exists)
  {
    std::cout << "Didn't create federation, it already existed" << std::endl;
  }
  catch (ErrorReadingFDD error)
  {
    std::wcout << error.what() << std::endl;
    return;
  }

  fedamb = std::make_shared<// @>ambassador>();

  mName = federateName;

  rtiamb->joinFederationExecution(convertStringToWstring(federateName), convertStringToWstring("ExampleFederation"), *fedamb);
  std::cout << "Joined Federation as " << federateName << std::endl;

  if ((mClient = socket(AF_INET, SOCK_STREAM, 0)) < 0)
  {
    std::cout << "Socket creation error" << std::endl;
    return;
  }

  mPort = port;
  struct sockaddr_in serv_addr;
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(port);

  // Convert IPv4 and IPv6 addresses from text to binary form
  if (inet_pton(AF_INET, HOST, &serv_addr.sin_addr) <= 0)
  {
    std::cout << "Invalid address/ Address not supported" << std::endl;
    return;
  }

  std::cout << "Connection to common server at " << HOST << ":" << port << std::endl;
  if (connect(mClient, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0)
  {
    std::cout << "Connection Failed" << std::endl;
    return;
  }


  dtig::MDTMessage message;
  dtig::MInitialize initializeMessage;
  initializeMessage.mutable_model_name()->set_value("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/experiments/fmi/BouncingBall.fmu");
  *message.mutable_initialize() = initializeMessage;

  auto initRet = SendMessage(message);
  if (initRet.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to initialize: " << initRet.error_message().value() << std::endl;
    return;
  }

  // @>callback(initialize)();

  rtiamb->registerFederationSynchronizationPoint(convertStringToWstring(READY_TO_RUN), toVariableLengthData(""));
  std::cout << "SynchronizationPoint registered" << std::endl;
  while (fedamb->isAnnounced == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  waitForUser();

  dtig::MDTMessage sMessage;
  dtig::MStart startMessage;
  startMessage.mutable_start_time()->set_value(0.0f);
  startMessage.mutable_stop_time()->set_value(5.0f);
  startMessage.set_run_mode(dtig::Run::STEP);
  *sMessage.mutable_start() = startMessage;

  auto startRet = SendMessage(sMessage);
  if (startRet.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to start: " << initRet.error_message().value() << std::endl;
    return;
  }

  rtiamb->synchronizationPointAchieved(convertStringToWstring(READY_TO_RUN));
  std::cout << "Achieved sync point: " << READY_TO_RUN << ", waiting for federation..." << std::endl;
  while (fedamb->isReadyToRun == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  enableTimePolicy();
  std::cout << "Time Policy Enabled" << std::endl;

  publishAndSubscribe();
  std::cout << "Published and Subscribed" << std::endl;

  ObjectInstanceHandle objectHandle = registerObject();

  dtig::MDTMessage aMessage;
  dtig::MAdvance advanceMessage;
  advanceMessage.mutable_step_size()->set_step(STEP);
  *aMessage.mutable_advance() = advanceMessage;

  while (true)
  {
    // @>callback(get_output)();

    auto ret = SendMessage(aMessage);
    if (ret.code() == dtig::ReturnCode::INVALID_STATE)
    {
      std::cout << "Stopped" << std::endl;
      break;
    }

    advanceTime(STEP);
    std::cout << "Time Advanced to " << fedamb->federateTime << std::endl;
  }

  waitForUser();

  dtig::MDTMessage stMessage;
  dtig::MStop stopMessage;
  stopMessage.set_mode(dtig::Stop::CLEAN);
  *stMessage.mutable_stop() = stopMessage;

  auto stopRet = SendMessage(stMessage);
  if (stopRet.code() != dtig::ReturnCode::SUCCESS)
    std::cout << "Failed to start: " << stopRet.error_message().value() << std::endl;

  deleteObject(objectHandle);

  rtiamb->resignFederationExecution(NO_ACTION);
  std::cout << "Resigned from Federation" << std::endl;

  try
  {
    rtiamb->destroyFederationExecution(L"ExampleFederation");
    std::cout << "Destroyed Federation" << std::endl;
  }
  catch (FederationExecutionDoesNotExist dne)
  {
    std::cout << "No need to destroy federation, it doesn't exist" << std::endl;
  }
  catch (FederatesCurrentlyJoined fcj)
  {
    std::cout << "Didn't destroy federation, federates still joined" << std::endl;
  }
}

// @method(private)
void waitForUser()
{
  std::cout << " >>>>>>>>>> Press Enter to Continue <<<<<<<<<<" << std::endl;
  (void)getchar();
}

// @method(private)
void enableTimePolicy()
{
  /////////////////////////////
  /// enable time regulation
  /////////////////////////////
  HLAfloat64Interval lookahead(fedamb->federateLookahead);
  rtiamb->enableTimeRegulation(lookahead);

  /// wait for callback
  while (fedamb->isRegulating == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  /////////////////////////////
  /// enable time constrained
  /////////////////////////////
  rtiamb->enableTimeConstrained();

  /// wait for callback
  while (fedamb->isConstrained == false)
  {
    rtiamb->evokeCallback(12.0);
  }
}

// @method(private)
void publishAndSubscribe()
{
  fedamb->attributeReceived = [this](rti1516::ObjectInstanceHandle theObject, const rti1516::AttributeHandleValueMap& theAttributeValues) {
    // @>callback(set_parameter)(theObject, theAttributeValues);
  };

  fedamb->interactionReceived = [this](rti1516::InteractionClassHandle theInteraction, const rti1516::ParameterHandleValueMap& theParameterValues) {
    // @>callback(set_input)(theInteraction, theParameterValues);
  };

  // @>callback(subscribe)();
  // @>callback(publish)();
}

// @method(private)
ObjectInstanceHandle registerObject()
{
  return rtiamb->registerObjectInstance(rtiamb->getObjectClassHandle(L"ObjectRoot.Parameters"));
}

// @method(private)
rti1516::VariableLengthData toVariableLengthData(const char* s)
{
  return toData(s);
}

// @method(private)
void updateAttributeValues(ObjectInstanceHandle objectHandle)
{
  // @>callback(get_parameter)(objectHandle);
}

// @method(private)
void advanceTime(double timestep)
{
  /// request the advance
  fedamb->isAdvancing = true;
  RTI1516fedTime newTime = (fedamb->federateTime + timestep);
  rtiamb->timeAdvanceRequest(newTime);

  /// wait for the time advance to be granted. ticking will tell the
  /// LRC to start delivering callbacks to the federate
  while (fedamb->isAdvancing)
  {
    rtiamb->evokeCallback(12.0);
  }
}

// @method(private)
void deleteObject(ObjectInstanceHandle objectHandle)
{
  rtiamb->deleteObjectInstance(objectHandle, toVariableLengthData(""));
}

// @method(private)
dtig::MReturnValue SendMessage(const google::protobuf::Message& message)
{
  dtig::MReturnValue result;

  auto toSend = message.SerializeAsString();
  send(mClient, toSend.c_str(), toSend.size(), 0);

  auto bytesRead = read(mClient, mBuffer, MSG_SIZE - 1);
  if (bytesRead <= 0)
  {
    result.set_code(dtig::ReturnCode::INVALID_STATE);
    result.mutable_error_message()->set_value("Server disconnected");
    return result;
  }

  if (!result.ParseFromArray(mBuffer, bytesRead))
  {
    result.set_code(dtig::ReturnCode::FAILURE);
    result.mutable_error_message()->set_value("Failed to parse response");
    return result;
  }

  return result;
}

// @main
#include <chrono>
#include <cstring>
#include <thread>

#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

int main(int argc, char *argv[])
{
  std::string federateName, fomPath, rtiAddress;
  char* port = "";
  bool name = false;
  bool fom = false;
  bool address = false;

  for (int i = 0; i < argc; i++)
  {
    if (strcmp(argv[i], "--name") == 0)
    {
        federateName = argv[i+1];
        name = true;
    }
    else if (strcmp(argv[i], "--fom") == 0)
    {
        fom = true;
        fomPath = argv[i+1];
    }
    else if (strcmp(argv[i], "--address") == 0)
    {
        address = true;
        rtiAddress = argv[i+1];
    }
    else if (strcmp(argv[i], "--port") == 0)
    {
      port = argv[i + 1];
    }
  }

  int child_status;
  pid_t childPid = fork();

  if (childPid == 0)
  {
    char* args[] = {"// @>server_cmd", "// @>server_path", port, NULL};

    // Start server
    if (execvp("// @>server_cmd", args) < 0)
    {
      std::cout << "Failed to start server" << std::endl;
      return -1;
    }
  }
  else if (childPid > 0)
  {
    // Give some time for the server to start
    std::this_thread::sleep_for(std::chrono::seconds(1));

    if (name && fom)
    {
      if (!address)
        rtiAddress = "127.0.0.1";

      // create and run the federate
      auto federate = std::make_shared<// @>classname>();
      federate->// @>run(federateName, fomPath, rtiAddress, std::stoi(port));

      waitpid(childPid, 0, 0);
    }
    else
    {
      if (!name)
        std::cout << "No name given" << std::endl;
      if (!fom)
        std::cout << "No FOM location given" << std::endl;
    }
  }
  else
  {
    std::cout << "Fork failed" << std::endl;
    return -1;
  }

  return 0;
}
