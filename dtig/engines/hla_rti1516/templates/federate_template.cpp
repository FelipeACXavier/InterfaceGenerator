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

#include "protobuf/dt_message.pb.h"
#include "protobuf/initialize.pb.h"
#include "protobuf/return_code.pb.h"
#include "protobuf/advance.pb.h"
#include "protobuf/start.pb.h"
#include "protobuf/stop.pb.h"
#include "protobuf/output.pb.h"
#include "protobuf/parameter.pb.h"

#define MSG_SIZE 1024
#define PORT 8080
#define HOST "127.0.0.1"

using namespace std;
using namespace rti1516;

static const double STEP = 0.01;

// @classname
HLAFederate

// @constructor
HLAFederate()
{
}

// @destructor
~HLAFederate()
{
  if (mClient >= 0)
    close(mClient);
}

// @method
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
  ///
  /// 1. create the RTIambassador
  ///
  rti1516::RTIambassadorFactory* factory = new rti1516::RTIambassadorFactory();
  std::vector<std::wstring> args;
  args.push_back(L"protocol=rti");
  args.push_back(L"address=" + convertStringToWstring(address));

  rtiamb = factory->createRTIambassador(args);

  ///
  /// 2. create and join to the federation
  /// NOTE: some other federate may have already created the federation,
  ///       in that case, we'll just try and join it
  ///
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

  /////////////////////////////
  /// 3. join the federation
  /////////////////////////////
  /// create the federate ambassador and join the federation
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


  dti::MDTMessage message;
  dti::MInitialize initializeMessage;
  initializeMessage.mutable_model_name()->set_value("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/experiments/fmi/BouncingBall.fmu");
  *message.mutable_initialize() = initializeMessage;

  auto initRet = SendMessage(message);
  if (initRet.code() != dti::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to initialize: " << initRet.error_message().value() << std::endl;
    return;
  }

  /// initialize the handles - have to wait until we are joined
  initializeHandles();

  /////////////////////////////////
  /// 4. announce the sync point
  /////////////////////////////////
  /// announce a sync point to get everyone on the same page. if the point
  /// has already been registered, we'll get a callback saying it failed,
  /// but we don't care about that, as long as someone registered it
  rtiamb->registerFederationSynchronizationPoint(convertStringToWstring(READY_TO_RUN), toVariableLengthData(""));
  std::cout << "SynchronizationPoint registered" << std::endl;
  while (fedamb->isAnnounced == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  /// WAIT FOR USER TO KICK US OFF.\n
  /// So that there is time to add other federates, we will wait until the
  /// user hits enter before proceeding. That was, you have time to start
  /// other federates.
  waitForUser();

  dti::MDTMessage sMessage;
  dti::MStart startMessage;
  startMessage.mutable_start_time()->mutable_fvalue()->set_value(0.0f);
  startMessage.mutable_stop_time()->mutable_fvalue()->set_value(5.0f);
  startMessage.set_run_mode(dti::Run::STEP);
  *sMessage.mutable_start() = startMessage;

  auto startRet = SendMessage(sMessage);
  if (startRet.code() != dti::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to start: " << initRet.error_message().value() << std::endl;
    return;
  }

  ////////////////////////////////////////////////////////
  /// 5. achieve the point and wait for synchronization
  ////////////////////////////////////////////////////////
  /// tell the RTI we are ready to move past the sync point and then wait
  /// until the federation has synchronized on
  rtiamb->synchronizationPointAchieved(convertStringToWstring(READY_TO_RUN));
  std::cout << "Achieved sync point: " << READY_TO_RUN << ", waiting for federation..." << std::endl;
  while (fedamb->isReadyToRun == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  /////////////////////////////
  // 6. enable time policies
  /////////////////////////////
  // in this section we enable/disable all time policies
  // note that this step is optional!
  enableTimePolicy();
  std::cout << "Time Policy Enabled" << std::endl;

  //////////////////////////////
  // 7. publish and subscribe
  //////////////////////////////
  // in this section we tell the RTI of all the data we are going to
  // produce, and all the data we want to know about
  publishAndSubscribe();
  std::cout << "Published and Subscribed" << std::endl;

  /////////////////////////////////////
  // 8. register an object to update
  /////////////////////////////////////
  ObjectInstanceHandle objectHandle = registerObject();

  dti::MDTMessage aMessage;
  dti::MAdvance advanceMessage;
  advanceMessage.mutable_step_size()->mutable_step()->mutable_fvalue()->set_value(STEP);
  *aMessage.mutable_advance() = advanceMessage;

  ////////////////////////////////////
  // 9. do the main simulation loop
  ////////////////////////////////////
  // here is where we do the meat of our work. in each iteration, we will
  // update the attribute values of the object we registered, and will
  // send an interaction.
  while (true)
  {
    sendInteraction();

    auto ret = SendMessage(aMessage);
    if (ret.code() == dti::ReturnCode::INVALID_STATE)
    {
      std::cout << "Stopped" << std::endl;
      break;
    }

    advanceTime(STEP);
    std::cout << "Time Advanced to " << fedamb->federateTime << std::endl;
  }

  waitForUser();

  dti::MDTMessage stMessage;
  dti::MStop stopMessage;
  stopMessage.set_mode(dti::Stop::CLEAN);
  *stMessage.mutable_stop() = stopMessage;

  auto stopRet = SendMessage(stMessage);
  if (stopRet.code() != dti::ReturnCode::SUCCESS)
    std::cout << "Failed to start: " << stopRet.error_message().value() << std::endl;

  //////////////////////////////////////
  // 10. delete the object we created
  //////////////////////////////////////
  deleteObject(objectHandle);

  ////////////////////////////////////
  // 11. resign from the federation
  ////////////////////////////////////
  rtiamb->resignFederationExecution(NO_ACTION);
  std::cout << "Resigned from Federation" << std::endl;

  ////////////////////////////////////////
  // 12. try and destroy the federation
  ////////////////////////////////////////
  // NOTE: we won't die if we can't do this because other federates
  //       remain. in that case we'll leave it for them to clean up
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

// @method
void initializeHandles()
{
  try
  {
    // @>callback(initialize)
  }
  catch (NameNotFound error)
  {
    std::wcout << "Failed to initialize handles: " << error.what() << std::endl;
  }
}

// @method
void waitForUser()
{
  std::cout << " >>>>>>>>>> Press Enter to Continue <<<<<<<<<<" << std::endl;
  (void)getchar();
}

// @method
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

// @method
void publishAndSubscribe()
{
  fedamb->attributeReceived = [this](rti1516::ObjectInstanceHandle theObject, const rti1516::AttributeHandleValueMap& theAttributeValues) {
    // @>callback(setparameter)(theObject, theAttributeValues);
  };

  fedamb->interactionReceived = [this](rti1516::InteractionClassHandle theInteraction, const rti1516::ParameterHandleValueMap& theParameterValues) {
    // @>callback(setinput)(theInteraction, theParameterValues);
  };

  // @>callback(subscribe)
  // @>callback(publish)
}

// @method
ObjectInstanceHandle registerObject()
{
  return rtiamb->registerObjectInstance(rtiamb->getObjectClassHandle(L"ObjectRoot.Parameters"));
}

// @method
rti1516::VariableLengthData toVariableLengthData(const char* s)
{
  return toData(s);
}

// @method
void updateAttributeValues(ObjectInstanceHandle objectHandle)
{
  // @>callback(getparameter)(objectHandle);
}

// @method
void sendInteraction()
{
  // @>callback(getoutput)();
}

// @method
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

// @method
void deleteObject(ObjectInstanceHandle objectHandle)
{
  rtiamb->deleteObjectInstance(objectHandle, toVariableLengthData(""));
}

// @method
double getLbts()
{
  return (fedamb->federateTime + fedamb->federateLookahead);
}

// @method
dti::MReturnValue SendMessage(const google::protobuf::Message& message)
{
  dti::MReturnValue result;

  auto toSend = message.SerializeAsString();
  send(mClient, toSend.c_str(), toSend.size(), 0);

  auto bytesRead = read(mClient, mBuffer, MSG_SIZE - 1);
  if (bytesRead <= 0)
  {
    result.set_code(dti::ReturnCode::INVALID_STATE);
    result.mutable_error_message()->set_value("Server disconnected");
    return result;
  }

  if (!result.ParseFromArray(mBuffer, bytesRead))
  {
    result.set_code(dti::ReturnCode::FAILURE);
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

#include "logging.h"

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