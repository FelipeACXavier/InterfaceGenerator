@imports
#include <RTI/LogicalTimeInterval.h>
#include <RTI/RTI1516fedTime.h>
#include <RTI/RTIambassador.h>
#include <RTI/RTIambassadorFactory.h>
#include <memory.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <iostream>

#include "logging.h"
#include "@ambassador_header"

using namespace std;
using namespace rti1516;

@classname
HLAFederate

@constructor
HLAFederate()
{
}

@destructor
~HLAFederate()
{
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
void runFederate(const std::string& federateName, const std::string& fom, const std::string& address)
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
  fedamb = std::make_shared<@ambassador>();

  mName = federateName;

  rtiamb->joinFederationExecution(convertStringToWstring(federateName), convertStringToWstring("ExampleFederation"), *fedamb.get());
  LOG_INFO("Joined Federation as %s", federateName.c_str());

  /// initialize the handles - have to wait until we are joined
  initializeHandles();

  LOG_INFO("Handles initialized");

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

  ////////////////////////////////////
  // 9. do the main simulation loop
  ////////////////////////////////////
  // here is where we do the meat of our work. in each iteration, we will
  // update the attribute values of the object we registered, and will
  // send an interaction.
  int i;
  for (i = 0; i < 20; i++)
  {
    /// 9.1 update the attribute values of the instance
    updateAttributeValues(objectHandle);

    /// 9.2 send an interaction
    sendInteraction();

    /// 9.3 request a time advance and wait until we get it
    advanceTime(1.0);
    LOG_INFO("Time Advanced to %.2lf", fedamb->federateTime);

    waitForUser();
  }

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

///////////////////////////////////////////////////////////////////////////////
//////////////////////////////// Helper Methods ///////////////////////////////
///////////////////////////////////////////////////////////////////////////////
@method
void initializeHandles()
{
  aHandle = rtiamb->getObjectClassHandle(L"HLAobjectRoot.A");

  aaHandle = rtiamb->getAttributeHandle(aHandle, L"aa");
  abHandle = rtiamb->getAttributeHandle(aHandle, L"ab");
  acHandle = rtiamb->getAttributeHandle(aHandle, L"ac");

  xHandle = rtiamb->getInteractionClassHandle(L"HLAinteractionRoot.X");

  xaHandle = rtiamb->getParameterHandle(xHandle, convertStringToWstring("xa"));
  xbHandle = rtiamb->getParameterHandle(xHandle, convertStringToWstring("xb"));
}

@method
void waitForUser()
{
  LOG_INFO(" >>>>>>>>>> Press Enter to Continue <<<<<<<<<<");
  string line;
  getline(cin, line);
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
  /////////////////////////////////////////////
  /// publish all attributes of ObjectRoot.A
  /////////////////////////////////////////////
  /// before we can register instance of the object class ObjectRoot.A and
  /// update the values of the various attributes, we need to tell the RTI
  /// that we intend to publish this information

  /// package the information into a handle set
  AttributeHandleSet attributes;
  attributes.insert(aaHandle);
  attributes.insert(abHandle);
  attributes.insert(acHandle);

  /// do the actual publication
  rtiamb->publishObjectClassAttributes(aHandle, attributes);

  //////////////////////////////////////////////////
  /// subscribe to all attributes of ObjectRoot.A
  //////////////////////////////////////////////////
  /// we also want to hear about the same sort of information as it is
  /// created and altered in other federates, so we need to subscribe to it
  rtiamb->subscribeObjectClassAttributes(aHandle, attributes, true);

  //////////////////////////////////////////////////////
  /// publish the interaction class InteractionRoot.X
  //////////////////////////////////////////////////////
  /// we want to send interactions of type InteractionRoot.X, so we need
  /// to tell the RTI that we're publishing it first. We don't need to
  /// inform it of the parameters, only the class, making it much simpler

  /// do the publication
  rtiamb->publishInteractionClass(xHandle);

  /////////////////////////////////////////////////////
  /// subscribe to the InteractionRoot.X interaction //
  /////////////////////////////////////////////////////
  /// we also want to receive other interaction of the same type that are
  /// sent out by other federates, so we have to subscribe to it first
  rtiamb->subscribeInteractionClass(xHandle);
}

@method
ObjectInstanceHandle registerObject()
{
  return rtiamb->registerObjectInstance(rtiamb->getObjectClassHandle(L"HLAobjectRoot.A"));
}

@method
rti1516::VariableLengthData toVariableLengthData(const char* s)
{
  rti1516::VariableLengthData variableLengthData;
  if (s)
    variableLengthData.setData(s, strlen(s));
  return variableLengthData;
}

@method
void updateAttributeValues(ObjectInstanceHandle objectHandle)
{
  ////////////////////////////////////////////////
  /// create the necessary container and values
  ///////////////////////////////////////////////
  /// create the collection to store the values in, as you can see
  /// this is quite a lot of work
  AttributeHandleValueMap attributes;

  /// generate the new values
  char aaValue[16], abValue[16], acValue[16];
  sprintf(aaValue, "aa:%f", getLbts());
  sprintf(abValue, "ab:%f", getLbts());
  sprintf(acValue, "ac:%f", getLbts());
  attributes[aaHandle] = toVariableLengthData(mName.c_str());
  attributes[abHandle] = toVariableLengthData(mName.c_str());
  attributes[acHandle] = toVariableLengthData(mName.c_str());

  ///////////////////////////
  /// do the actual update
  ///////////////////////////
  LOG_INFO("Attribute: %s %s %s", aaValue, abValue, acValue);
  rtiamb->updateAttributeValues(objectHandle, attributes, toVariableLengthData("hi!"));

  /// note that if you want to associate a particular timestamp with the
  /// update. here we send another update, this time with a timestamp:
  RTI1516fedTime time = fedamb->federateTime + fedamb->federateLookahead;
  LOG_INFO("Timed attribute: %s %s %s", aaValue, abValue, acValue);
  rtiamb->updateAttributeValues(objectHandle, attributes, toVariableLengthData("hi!"), time);
}

@method
void sendInteraction()
{
  ////////////////////////////////////////////////
  /// create the necessary container and values
  ////////////////////////////////////////////////
  /// create the collection to store the values in
  ParameterHandleValueMap parameters;

  /// generate the new values
  char xaValue[16], xbValue[16];
  sprintf(xaValue, "xa:%f", getLbts());
  sprintf(xbValue, "xb:%f", getLbts());
  parameters[xaHandle] = toVariableLengthData(xaValue);
  parameters[xbHandle] = toVariableLengthData(xbValue);

  ///////////////////////////
  /// send the interaction
  ///////////////////////////
  LOG_INFO("Interaction: %s %s", xaValue, xbValue);
  rtiamb->sendInteraction(xHandle, parameters, toVariableLengthData("hi!"));

  /// if you want to associate a particular timestamp with the
  /// interaction, you will have to supply it to the RTI. Here
  /// we send another interaction, this time with a timestamp:
  RTI1516fedTime time = fedamb->federateTime + fedamb->federateLookahead;
  LOG_INFO("Timed interaction: %s %s", xaValue, xbValue);
  rtiamb->sendInteraction(xHandle, parameters, toVariableLengthData("hi!"), time);
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

@main
#include <cstring>

int main(int argc, char *argv[])
{
  std::string federateName, fomPath, rtiAddress;
  bool name = false;
  bool fom = false;
  bool address = false;

  for (int i=0; i < argc; i++)
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
  }

  // create and run the federate
  auto federate = std::shared_ptr<@classname>();

  if (name && fom)
  {
    if (!address)
      rtiAddress = "127.0.0.1";

    auto federate = std::shared_ptr<@classname>();
    federate->@run(federateName, fomPath, rtiAddress);
  }
  else
  {
    if (!name)
      printf("No name given\n");
    if (!fom)
      printf("No FOM location given\n");
  }

  return 0;
}