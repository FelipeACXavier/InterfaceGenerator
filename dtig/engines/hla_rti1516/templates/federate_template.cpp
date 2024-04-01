@imports
#include <RTI/LogicalTimeInterval.h>
#include <RTI/RTI1516fedTime.h>
#include <RTI/RTIambassador.h>
#include <RTI/RTIambassadorFactory.h>

#include <locale>
#include <codecvt>
#include <memory>

#include <string.h>

#include "logging.h"
#include "@>ambassador_header"

#include "protobuf/dt_message.pb.h"
#include "protobuf/initialize.pb.h"
#include "protobuf/return_code.pb.h"
#include "protobuf/advance.pb.h"
#include "protobuf/start.pb.h"
#include "protobuf/stop.pb.h"
#include "protobuf/output.pb.h"

#define PORT 8080
#define HOST "127.0.0.1"

using namespace std;
using namespace rti1516;

static const float STEP = 0.05;

@classname
HLAFederate

@constructor
HLAFederate()
{
}

@destructor
~HLAFederate()
{
  if (mClient >= 0)
    close(mClient);
}

@method
std::wstring convertStringToWstring(const std::string& str)
{
  const std::ctype<wchar_t>& CType = std::use_facet<std::ctype<wchar_t> >(std::locale());
  std::vector<wchar_t> wideStringBuffer(str.length());
  CType.widen(str.data(), str.data() + str.length(), &wideStringBuffer[0]);
  return std::wstring(&wideStringBuffer[0], wideStringBuffer.size());
}

@run
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
    LOG_INFO("Created Federation");
  }
  catch (FederationExecutionAlreadyExists exists)
  {
    LOG_INFO("Didn't create federation, it already existed");
  }
  catch (ErrorReadingFDD error)
  {
    LOG_ERROR("%s", error.what().c_str());
    return;
  }

  /////////////////////////////
  /// 3. join the federation
  /////////////////////////////
  /// create the federate ambassador and join the federation
  fedamb = std::make_shared<@>ambassador>();

  mName = federateName;

  rtiamb->joinFederationExecution(convertStringToWstring(federateName), convertStringToWstring("ExampleFederation"), *fedamb);
  LOG_INFO("Joined Federation as %s", federateName.c_str());

  if ((mClient = socket(AF_INET, SOCK_STREAM, 0)) < 0)
  {
    LOG_ERROR("Socket creation error");
    return;
  }

  mPort = port;
  struct sockaddr_in serv_addr;
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(port);

  // Convert IPv4 and IPv6 addresses from text to binary form
  if (inet_pton(AF_INET, HOST, &serv_addr.sin_addr) <= 0)
  {
    LOG_ERROR("Invalid address/ Address not supported");
    return;
  }

  LOG_INFO("Connection to common server at %s:%u", HOST, port);
  if (connect(mClient, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0)
  {
    LOG_ERROR("Connection Failed");
    return;
  }


  dti::MDTMessage message;
  dti::MInitialize initializeMessage;
  initializeMessage.mutable_model_name()->set_value("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/experiments/fmi/BouncingBall.fmu");
  *message.mutable_initialize() = initializeMessage;

  auto initRet = SendMessage(message);
  if (initRet.code() != dti::ReturnCode::SUCCESS)
  {
    LOG_ERROR("Failed to initialize: %s", initRet.error_message().value().c_str());
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
  LOG_INFO("SynchronizationPoint registered");
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
    LOG_ERROR("Failed to start: %s", startRet.error_message().value().c_str());
    return;
  }

  ////////////////////////////////////////////////////////
  /// 5. achieve the point and wait for synchronization
  ////////////////////////////////////////////////////////
  /// tell the RTI we are ready to move past the sync point and then wait
  /// until the federation has synchronized on
  rtiamb->synchronizationPointAchieved(convertStringToWstring(READY_TO_RUN));
  LOG_INFO("Achieved sync point: %s, waiting for federation...", READY_TO_RUN);
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
  LOG_INFO("Time Policy Enabled");

  //////////////////////////////
  // 7. publish and subscribe
  //////////////////////////////
  // in this section we tell the RTI of all the data we are going to
  // produce, and all the data we want to know about
  publishAndSubscribe();
  LOG_INFO("Published and Subscribed");

  /////////////////////////////////////
  // 8. register an object to update
  /////////////////////////////////////
  ObjectInstanceHandle objectHandle = registerObject();
  LOG_INFO("Registered Object, handle=%ls", objectHandle.toString().c_str());

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
    auto ret = SendMessage(aMessage);
    if (ret.code() == dti::ReturnCode::INVALID_STATE)
    {
      LOG_WARNING("Stopped");
      break;
    }

    sendInteraction();

    advanceTime(STEP);
    LOG_INFO("Time Advanced to %.2lf", fedamb->federateTime);
  }

  waitForUser();

  dti::MDTMessage stMessage;
  dti::MStop stopMessage;
  stopMessage.set_mode(dti::Stop::CLEAN);
  *stMessage.mutable_stop() = stopMessage;

  auto stopRet = SendMessage(stMessage);
  if (stopRet.code() != dti::ReturnCode::SUCCESS)
    LOG_ERROR("Failed to stop: %s", stopRet.error_message().value().c_str());
  else
    LOG_INFO("Stopped server");
  //////////////////////////////////////
  // 10. delete the object we created
  //////////////////////////////////////
  deleteObject(objectHandle);
  LOG_INFO("Deleted Object, handle=%ls", objectHandle.toString().c_str());

  ////////////////////////////////////
  // 11. resign from the federation
  ////////////////////////////////////
  rtiamb->resignFederationExecution(NO_ACTION);
  LOG_INFO("Resigned from Federation");

  ////////////////////////////////////////
  // 12. try and destroy the federation
  ////////////////////////////////////////
  // NOTE: we won't die if we can't do this because other federates
  //       remain. in that case we'll leave it for them to clean up
  try
  {
    rtiamb->destroyFederationExecution(L"ExampleFederation");
    LOG_INFO("Destroyed Federation");
  }
  catch (FederationExecutionDoesNotExist dne)
  {
    LOG_INFO("No need to destroy federation, it doesn't exist");
  }
  catch (FederatesCurrentlyJoined fcj)
  {
    LOG_INFO("Didn't destroy federation, federates still joined");
  }
}

@method
void initializeHandles()
{
  try
  {
    @>callback(initialize)
  }
  catch (NameNotFound error)
  {
    LOG_ERROR("Could not find: %s", error.what().c_str());
  }
}

@method
void waitForUser()
{
  LOG_INFO(" >>>>>>>>>> Press Enter to Continue <<<<<<<<<<");
  (void)getchar();
}

@method
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

@method
void publishAndSubscribe()
{
  fedamb->attributeReceived = [this](rti1516::ObjectInstanceHandle theObject, const rti1516::AttributeHandleValueMap& theAttributeValues) {
    std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;
    auto object = converter.to_bytes(theObject.toString());
    LOG_INFO("Attribute received handle=%s, count=%u", object.c_str(), theAttributeValues.size());

    for (auto i = theAttributeValues.begin(); i != theAttributeValues.end(); i++)
    {
      std::string param = converter.to_bytes(i->first.toString());
      std::string value = std::string((char*)i->second.data(), i->second.size());
      LOG_INFO("attrHandle=%s, attrValue=%s", param.c_str(), value.c_str());
    }

    LOG_INFO("");
  };

  fedamb->interactionReceived = [this](rti1516::InteractionClassHandle theInteraction, const rti1516::ParameterHandleValueMap& theParameterValues) {
    @>callback(setinput)(theInteraction, theParameterValues);
  };

  @>callback(subscribe)
}

@method
ObjectInstanceHandle registerObject()
{
  return rtiamb->registerObjectInstance(rtiamb->getObjectClassHandle(L"ObjectRoot.Parameters"));
}

@method
rti1516::VariableLengthData toVariableLengthData(const char* s)
{
  // rti1516::VariableLengthData variableLengthData;
  // if (s)
  //   variableLengthData.setData(s, strlen(s));
  return toData(s);
}

@method
void updateAttributeValues(ObjectInstanceHandle objectHandle)
{
  ////////////////////////////////////////////////
  /// create the necessary container and values
  ///////////////////////////////////////////////
  /// create the collection to store the values in, as you can see
  /// this is quite a lot of work
  // AttributeHandleValueMap attributes;

  /// generate the new values
  // char aaValue[16], abValue[16], acValue[16];
  // sprintf(aaValue, "aa:%f", getLbts());
  // sprintf(abValue, "ab:%f", getLbts());
  // sprintf(acValue, "ac:%f", getLbts());
  // attributes[aaHandle] = toVariableLengthData(mName.c_str());
  // attributes[abHandle] = toVariableLengthData(mName.c_str());
  // attributes[acHandle] = toVariableLengthData(mName.c_str());

  ///////////////////////////
  /// do the actual update
  ///////////////////////////
  // LOG_INFO("Attribute: %s %s %s", aaValue, abValue, acValue);
  // rtiamb->updateAttributeValues(objectHandle, attributes, toVariableLengthData("hi!"));

  // /// note that if you want to associate a particular timestamp with the
  // /// update. here we send another update, this time with a timestamp:
  // RTI1516fedTime time = fedamb->federateTime + fedamb->federateLookahead;
  // LOG_INFO("Timed attribute: %s %s %s", aaValue, abValue, acValue);
  // rtiamb->updateAttributeValues(objectHandle, attributes, toVariableLengthData("hi!"), time);
}

@method
void sendInteraction()
{
  @>callback(getoutput)();
}

@method
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

@method
void deleteObject(ObjectInstanceHandle objectHandle)
{
  rtiamb->deleteObjectInstance(objectHandle, toVariableLengthData(""));
}

@method
double getLbts()
{
  return (fedamb->federateTime + fedamb->federateLookahead);
}

@method
dti::MReturnValue SendMessage(const google::protobuf::Message& message)
{
  dti::MReturnValue result;

  auto toSend = message.SerializeAsString();
  send(mClient, toSend.c_str(), toSend.size(), 0);

  char buffer[1024] = {0};
  if (read(mClient, buffer, 1024 - 1) <= 0)
  {
    result.set_code(dti::ReturnCode::INVALID_STATE);
    result.mutable_error_message()->set_value("Server disconnected");
    return result;
  }

  std::string s(buffer);
  if (!result.ParseFromString(s))
  {
    result.set_code(dti::ReturnCode::FAILURE);
    result.mutable_error_message()->set_value("Failed to parse response");
    return result;
  }

  return result;
}

@main
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
    char* args[] = {"@>server_cmd", "@>server_path", port, NULL};

    // Start server
    if (execvp("@>server_cmd", args) < 0)
    {
      LOG_ERROR("Failed to start server");
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
      auto federate = std::make_shared<@>classname>();
      federate->@>run(federateName, fomPath, rtiAddress, std::stoi(port));

      waitpid(childPid, 0, 0);
    }
    else
    {
      if (!name)
        LOG_ERROR("No name given");
      if (!fom)
        LOG_ERROR("No FOM location given");
    }
  }
  else
  {
    LOG_ERROR("Fork failed");
    return -1;
  }

  return 0;
}