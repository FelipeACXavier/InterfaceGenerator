<DTIG_IMPORTS>
#include <RTI/LogicalTimeInterval.h>
#include <RTI/RTI1516fedTime.h>
#include <RTI/RTIambassador.h>
#include <RTI/RTIambassadorFactory.h>

#include <algorithm>
#include <locale>
#include <codecvt>
#include <memory>

#include <chrono>
#include <string>
#include <thread>

#include "DTIG>AMBASSADOR_HEADER"

#include "dtig/dt_message.pb.h"
#include "dtig/initialize.pb.h"
#include "dtig/return_code.pb.h"
#include "dtig/advance.pb.h"
#include "dtig/start.pb.h"
#include "dtig/stop.pb.h"
#include "dtig/state.pb.h"
#include "dtig/output.pb.h"
#include "dtig/get_status.pb.h"
#include "dtig/set_parameter.pb.h"
#include "dtig/get_parameter.pb.h"

#define MSG_SIZE 1024
#define PORT 8080
#define HOST "127.0.0.1"

using namespace std;
using namespace rti1516;

static const double STEP = 0.02;
static const double STOP_TIME = 5.0;

<DTIG_CLASSNAME>
HLAFederate

<DTIG_CONSTRUCTOR(PUBLIC)>
HLAFederate()
{
}

<DTIG_DESTRUCTOR(PUBLIC)>
~HLAFederate()
{
  if (mClient >= 0)
    close(mClient);
}

<DTIG_METHOD(PRIVATE)>
std::wstring convertStringToWstring(const std::string& str)
{
  const std::ctype<wchar_t>& CType = std::use_facet<std::ctype<wchar_t> >(std::locale());
  std::vector<wchar_t> wideStringBuffer(str.length());
  CType.widen(str.data(), str.data() + str.length(), &wideStringBuffer[0]);
  return std::wstring(&wideStringBuffer[0], wideStringBuffer.size());
}

<DTIG_RUN>
void runFederate(const std::string& federateName, const std::string& fom, const std::string& address, uint32_t port)
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

  fedamb = std::make_shared<DTIG>AMBASSADOR>();

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
  initializeMessage.mutable_model_name()->set_value("BouncingBall");
  *message.mutable_initialize() = initializeMessage;

  auto initRet = SendMessage(message);
  if (initRet.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to initialize: " << initRet.error_message().value() << std::endl;
    return;
  }

  DTIG>CALLBACK(INITIALIZE)();

  rtiamb->registerFederationSynchronizationPoint(convertStringToWstring(READY_TO_RUN), toVariableLengthData(""));
  std::cout << "SynchronizationPoint registered" << std::endl;
  while (fedamb->isAnnounced == false)
  {
    rtiamb->evokeCallback(12.0);
  }

  std::cout << "Initialized model. Continue?" << std::endl;
  waitForUser();

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


  dtig::MDTMessage sMessage;
  dtig::MStart startMessage;
  startMessage.mutable_start_time()->set_value(0.0f);
  startMessage.mutable_stop_time()->set_value(STOP_TIME);
  startMessage.mutable_step_size()->set_step(STEP);
  startMessage.set_run_mode(dtig::Run::STEPPED);
  *sMessage.mutable_start() = startMessage;

  dtig::MDTMessage statusMessage;
  dtig::MGetStatus getStatus;
  getStatus.set_request(true);
  *statusMessage.mutable_get_status() = getStatus;

  std::cout << "Start?" << std::endl;
  waitForUser();

  auto startRet = SendMessage(sMessage);
  if (startRet.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to start: " << initRet.error_message().value() << std::endl;
    return;
  }

  std::cout << "Waiting for model to start" << std::endl;
  dtig::MReturnValue ret;
  do
  {
    ret = SendMessage(statusMessage);
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
  } while (ret.has_status() &&
           ret.status().state() != dtig::State::EState::RUNNING &&
           ret.status().state() != dtig::State::EState::WAITING &&
           ret.status().state() != dtig::State::EState::STOPPED);

  dtig::MDTMessage aMessage;
  dtig::MAdvance advanceMessage;
  advanceMessage.mutable_step_size()->set_step(STEP);
  *aMessage.mutable_advance() = advanceMessage;

  std::cout << "Starting loop" << std::endl;
  while (fedamb->federateTime < STOP_TIME)
  {
    // Wait until model is ready to advance
    dtig::MReturnValue ret;
    do
    {
      ret = SendMessage(statusMessage);
      std::this_thread::sleep_for(std::chrono::microseconds(20));
    } while (ret.has_status() && ret.status().state() == dtig::State::EState::RUNNING);

    DTIG>CALLBACK(GET_OUTPUT)();

    ret = SendMessage(aMessage);
    if (ret.code() != dtig::ReturnCode::SUCCESS)
    {
      std::cout << "Stopped: " << ret.error_message().value() << std::endl;
      break;
    }

    advanceTime(STEP);
    std::cout << "Time Advanced to " << fedamb->federateTime << std::endl;
  }

  std::cout << "Simulation done: " << fedamb->federateTime << std::endl;
  waitForUser();

  dtig::MDTMessage dtMessage;
  dtig::MStop stopMessage;
  stopMessage.set_mode(dtig::Stop::CLEAN);
  *dtMessage.mutable_stop() = stopMessage;

  auto stopRet = SendMessage(dtMessage);
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

<DTIG_METHOD(PRIVATE)>
void waitForUser()
{
  std::cout << " >>>>>>>>>> Press Enter to Continue <<<<<<<<<<" << std::endl;
  (void)getchar();
}

<DTIG_METHOD(PRIVATE)>
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

<DTIG_METHOD(PRIVATE)>
void publishAndSubscribe()
{
  fedamb->attributeReceived = [this](rti1516::ObjectInstanceHandle theObject, const rti1516::AttributeHandleValueMap& theAttributeValues) {
    DTIG>CALLBACK(SET_PARAMETER)(theObject, theAttributeValues);
  };

  fedamb->interactionReceived = [this](rti1516::InteractionClassHandle theInteraction, const rti1516::ParameterHandleValueMap& theParameterValues) {
    DTIG>CALLBACK(SET_INPUT)(theInteraction, theParameterValues);
  };

  DTIG>CALLBACK(SUBSCRIBE)();
  DTIG>CALLBACK(PUBLISH)();
}

<DTIG_METHOD(PRIVATE)>
ObjectInstanceHandle registerObject()
{
  return rtiamb->registerObjectInstance(rtiamb->getObjectClassHandle(L"ObjectRoot.Parameters"));
}

<DTIG_METHOD(PRIVATE)>
rti1516::VariableLengthData toVariableLengthData(const char* s)
{
  return toData(s);
}

<DTIG_METHOD(PRIVATE)>
void updateAttributeValues(ObjectInstanceHandle objectHandle)
{
  DTIG>CALLBACK(GET_PARAMETER)(objectHandle);
}

<DTIG_METHOD(PRIVATE)>
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

<DTIG_METHOD(PRIVATE)>
void deleteObject(ObjectInstanceHandle objectHandle)
{
  rtiamb->deleteObjectInstance(objectHandle, toVariableLengthData(""));
}

<DTIG_METHOD(PRIVATE)>
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

<DTIG_MAIN>
#include <chrono>
#include <cstring>
#include <thread>

#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

int main(int argc, char *argv[])
{
  std::string federateName, fomPath, rtiAddress;
  std::string port;
  bool name = false;
  bool fom = false;
  bool address = false;

  for (int i = 0; i < argc; i++)
  {
    if (strcmp(argv[i], "--name") == 0)
    {
        federateName = argv[i + 1];
        name = true;
    }
    else if (strcmp(argv[i], "--fom") == 0)
    {
        fom = true;
        fomPath = argv[i + 1];
    }
    else if (strcmp(argv[i], "--address") == 0)
    {
        address = true;
        rtiAddress = argv[i + 1];
    }
    else if (strcmp(argv[i], "--port") == 0)
    {
      port = argv[i + 1];
    }
  }

  int child_status;
  pid_t childPid = 1; // fork();

  if (childPid > 0)
  {
    // Give some time for the server to start
    // std::this_thread::sleep_for(std::chrono::seconds(1));

    if (name && fom)
    {
      if (!address)
        rtiAddress = "127.0.0.1";

      // create and run the federate
      auto federate = std::make_shared<DTIG>CLASSNAME>();
      federate->DTIG>RUN(federateName, fomPath, rtiAddress, std::stoi(port));

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

<DTIG_CALLBACK(INITIALIZE)>
void initializeHandles()
{
  try
  {
    DTIG_FOR(DTIG_PARAMETERS)
    DTIG_IF(DTIG_INDEX == 0)

    mAttributeHandler = rtiamb->getObjectClassHandle(L"DTIG_ITEM_NAMESPACE");
    DTIG_END_IF
    mAttributeHandlers.insert({DTIG_STR(DTIG_ITEM_NAME), rtiamb->getAttributeHandle(mAttributeHandler, L"DTIG_ITEM_NAME")});

    DTIG_END_FOR

    DTIG_FOR(DTIG_INPUTS)
    DTIG_IF(DTIG_INDEX == 0)

    mInputHandler = rtiamb->getInteractionClassHandle(L"DTIG_ITEM_NAMESPACE");
    DTIG_END_IF
    mInputHandlers.insert({rtiamb->getParameterHandle(mInputHandler, L"DTIG_ITEM_NAME"), DTIG_STR(DTIG_ITEM_NAME)});
    DTIG_END_FOR

    DTIG_FOR(DTIG_OUTPUTS)
    DTIG_IF(DTIG_INDEX == 0)

    mOutputHandler = rtiamb->getInteractionClassHandle(L"DTIG_ITEM_NAMESPACE");
    DTIG_END_IF
    mOutputHandlers.insert({DTIG_STR(DTIG_ITEM_NAME), rtiamb->getParameterHandle(mOutputHandler, L"DTIG_ITEM_NAME")});
    DTIG_END_FOR
  }
  catch (NameNotFound error)
  {
    std::wcout << "Failed to initialize handles: " << error.what() << std::endl;
  }
}

<DTIG_CALLBACK(SET_INPUT)>
void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues)
{
  dtig::MInput inputMessage;

  for (auto it = parameterValues.begin(); it != parameterValues.end(); ++it)
  {
    std::string item = mInputHandlers[it->first];
    *inputMessage.mutable_inputs()->add_identifiers() = item;
    DTIG_FOR(DTIG_INPUTS)
    DTIG_IF(DTIG_INDEX == 0)
    if (item == DTIG_STR(DTIG_ITEM_NAME))
    DTIG_ELSE
    else if (item == DTIG_STR(DTIG_ITEM_NAME))
    DTIG_END_IF
    {
      DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) value;
      value.set_value(fromData<DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)>(it->second));
      inputMessage.mutable_inputs()->add_values()->PackFrom(value);
    }
    DTIG_END_FOR
    else
    {
      std::cout << "Unknown input: " << item << std::endl;
      return;
    }
  }

  dtig::MDTMessage message;
  *message.mutable_set_input() = inputMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
    std::cout << "Failed to set inputs: " << ret.error_message().value() << std::endl;
}

<DTIG_CALLBACK(GET_OUTPUT)>
void GetOutput()
{
  dtig::MOutput outputMessage;
  DTIG_IF(DTIG_OUTPUTS)
  DTIG_FOR(DTIG_OUTPUTS)
  *outputMessage.mutable_outputs()->add_identifiers() = DTIG_STR(DTIG_ITEM_NAME);
  DTIG_END_FOR

  dtig::MDTMessage message;
  *message.mutable_get_output() = outputMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to get outputs: " << ret.error_message().value() << std::endl;
    return;
  }

  ParameterHandleValueMap parameters;
  DTIG_FOR(DTIG_OUTPUTS)

  std::string idDTIG_ITEM_NAME = ret.values().identifiers(DTIG_INDEX);
  DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) valueDTIG_ITEM_NAME;
  if (ret.values().values(DTIG_INDEX).UnpackTo(&valueDTIG_ITEM_NAME))
  {
    DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE) vDTIG_ITEM_NAME = valueDTIG_ITEM_NAME.value();
    parameters[mOutputHandlers.at(idDTIG_ITEM_NAME)] = toData<DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)>(&vDTIG_ITEM_NAME);
  }
  else
  {
    std::cout << "Failed to unpack output: DTIG_ITEM_NAME" << std::endl;
  }

  DTIG_END_FOR

  rtiamb->sendInteraction(mOutputHandler, parameters, toVariableLengthData(mName.c_str()));
  DTIG_END_IF
}

<DTIG_METHOD(PUBLIC)>
std::string getAttribute(const rti1516::AttributeHandle& handle) const
{
  for (auto it = mAttributeHandlers.begin(); it != mAttributeHandlers.end(); ++it)
    if (it->second == handle)
      return it->first;

  return std::string();
}

<DTIG_CALLBACK(SET_PARAMETER)>
void SetParameters(const rti1516::ObjectInstanceHandle& object, const rti1516::AttributeHandleValueMap& attributes)
{
  dtig::MSetParameter paramMessage;

  for (auto it = attributes.begin(); it != attributes.end(); ++it)
  {
    std::string item = getAttribute(it->first);
    if (item.empty())
      continue;

    *paramMessage.mutable_parameters()->add_identifiers() = item;
    DTIG_FOR(DTIG_PARAMETERS)
    DTIG_IF(DTIG_INDEX == 0)
    if (item == DTIG_STR(DTIG_ITEM_NAME))
    DTIG_ELSE
    else if (item == DTIG_STR(DTIG_ITEM_NAME))
    DTIG_END_IF
    {
      DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) value;
      value.set_value(fromData<DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)>(it->second));
      paramMessage.mutable_parameters()->add_values()->PackFrom(value);
    }
    DTIG_END_FOR
    else
    {
      std::cout << "Unknown parameter: " << item << std::endl;
      return;
    }
  }

  dtig::MDTMessage message;
  *message.mutable_set_parameter() = paramMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
    std::cout << "Failed to set parameters: " << ret.error_message().value() << std::endl;
}

<DTIG_CALLBACK(GET_PARAMETER)>
void GetParameter(const ObjectInstanceHandle& handler)
{
  DTIG_IF(DTIG_PARAMETERS)
  dtig::MGetParameter paramMessage;
  DTIG_FOR(DTIG_PARAMETERS)
  *paramMessage.mutable_parameters()->add_identifiers() = DTIG_STR(DTIG_ITEM_NAME);
  DTIG_END_FOR

  dtig::MDTMessage message;
  *message.mutable_get_parameter() = paramMessage;
  dtig::MReturnValue ret = SendMessage(message);
  if (ret.code() != dtig::ReturnCode::SUCCESS)
  {
    std::cout << "Failed to get parameters: " << ret.error_message().value() << std::endl;
    return;
  }

  AttributeHandleValueMap attributesMap;
  DTIG_FOR(DTIG_PARAMETERS)

  std::string idDTIG_ITEM_NAME = ret.values().identifiers(DTIG_INDEX);
  DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) valueDTIG_ITEM_NAME;
  if (ret.values().values(DTIG_INDEX).UnpackTo(&valueDTIG_ITEM_NAME))
  {
    DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE) vDTIG_ITEM_NAME = valueDTIG_ITEM_NAME.value();
    attributesMap[mAttributeHandlers.at(idDTIG_ITEM_NAME)] = toData<DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)>(&vDTIG_ITEM_NAME);
  }
  else
  {
    std::cout << "Failed to unpack parameter: DTIG_ITEM_NAME" << std::endl;
  }
  DTIG_END_FOR

  rtiamb->updateAttributeValues(handler, attributesMap, toVariableLengthData(mName.c_str()));
  DTIG_END_IF
}

<DTIG_CALLBACK(PUBLISH)>
void SetupPublishers()
{
  DTIG_IF(DTIG_PARAMETERS)
  AttributeHandleSet pubAttributes;
  for (const auto& pair : mAttributeHandlers)
    pubAttributes.insert(pair.second);

  rtiamb->publishObjectClassAttributes(mAttributeHandler, pubAttributes);
  DTIG_END_IF

  DTIG_IF(DTIG_OUTPUTS)
  rtiamb->publishInteractionClass(mOutputHandler);
  DTIG_END_IF
}

<DTIG_CALLBACK(SUBSCRIBE)>
void SetupSubscribers()
{
  DTIG_IF(DTIG_PARAMETERS)
  AttributeHandleSet subAttributes;
  for (const auto& pair : mAttributeHandlers)
    subAttributes.insert(pair.second);

  rtiamb->subscribeObjectClassAttributes(mAttributeHandler, subAttributes, true);
  DTIG_END_IF

  DTIG_IF(DTIG_INPUTS)
  rtiamb->subscribeInteractionClass(mInputHandler);
  DTIG_END_IF
}
