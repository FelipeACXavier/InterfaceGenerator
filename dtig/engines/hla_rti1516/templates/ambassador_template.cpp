@imports
#include <RTI/RTI1516fedTime.h>
#include <string.h>

#include <iostream>
#include "logging.h"

using namespace rti1516;

@classname
HLAAmbassador

@constructor
HLAAmbassador()
{
  // initialize all the variable values
  federateTime = 0.0;
  federateLookahead = 1.0;

  isRegulating = false;
  isConstrained = false;
  isAdvancing = false;
  isAnnounced = false;
  isReadyToRun = false;
}

@destructor
~HLAAmbassador() throw()
{
}

@method
double convertTime(LogicalTime const& theTime)
{
  RTI1516fedTime castedTime = (RTI1516fedTime)theTime;
  return castedTime.getFedTime();
}

@method
void synchronizationPointRegistrationSucceeded(std::wstring const& label) throw(FederateInternalError)
{
  std::wcout << "Successfully registered sync point: " << label << std::endl;
}

@method
void synchronizationPointRegistrationFailed(std::wstring const& label, SynchronizationFailureReason reason) throw(FederateInternalError)
{
  std::wcout << "Failed to register sync point: " << label << std::endl;
}

@method
void announceSynchronizationPoint(std::wstring const& label, VariableLengthData const& theUserSuppliedTag) throw(FederateInternalError)
{
  std::wcout << "Synchronization point announced: " << label << std::endl;

  std::wstring compare = L"ReadyToRun";
  if (wcscmp(label.c_str(), compare.c_str()) == 0)
    this->isAnnounced = true;
}

@method
void federationSynchronized(std::wstring const& label) throw(FederateInternalError)
{
  std::wcout << "Federation Synchronized: " << label << std::endl;
  std::wstring compair = L"ReadyToRun";
  if (wcscmp(label.c_str(), compair.c_str()) == 0)
    this->isReadyToRun = true;
}

@method
void timeRegulationEnabled(LogicalTime const& theFederateTime) throw(InvalidLogicalTime,
                                                                                    NoRequestToEnableTimeRegulationWasPending,
                                                                                    FederateInternalError)
{
  this->isRegulating = true;
  this->federateTime = convertTime(theFederateTime);
}

@method
void timeConstrainedEnabled(LogicalTime const& theFederateTime) throw(InvalidLogicalTime,
                                                                                     NoRequestToEnableTimeConstrainedWasPending,
                                                                                     FederateInternalError)
{
  this->isConstrained = true;
  this->federateTime = convertTime(theFederateTime);
}

@method
void timeAdvanceGrant(LogicalTime const& theTime) throw(InvalidLogicalTime,
                                                        JoinedFederateIsNotInTimeAdvancingState,
                                                        FederateInternalError)
{
  this->isAdvancing = false;
  this->federateTime = convertTime(theTime);
}

@method
void discoverObjectInstance(ObjectInstanceHandle theObject,
                            ObjectClassHandle theObjectClass,
                            std::wstring const& theObjectInstanceName) throw(CouldNotDiscover,
                                                                             ObjectClassNotKnown,
                                                                             FederateInternalError)
{
  LOG_INFO("Discovered Object: handle= %ls, classHandle=%ls, name=%ls",
    theObject.toString().c_str(),
    theObjectClass.toString().c_str(),
    theObjectInstanceName.c_str());
}

@method
void reflectAttributeValues(ObjectInstanceHandle theObject,
                            AttributeHandleValueMap const& theAttributeValues,
                            VariableLengthData const& theUserSuppliedTag,
                            OrderType sentOrder,
                            TransportationType theType) throw(ObjectInstanceNotKnown,
                                                              AttributeNotRecognized,
                                                              AttributeNotSubscribed,
                                                              FederateInternalError)
{
  if (attributeReceived)
    attributeReceived(theObject, theAttributeValues);
}

@method
void reflectAttributeValues(ObjectInstanceHandle theObject,
                            AttributeHandleValueMap const& theAttributeValues,
                            VariableLengthData const& theUserSuppliedTag,
                            OrderType sentOrder,
                            TransportationType theType,
                            RegionHandleSet const& theSentRegionHandleSet) throw(ObjectInstanceNotKnown,
                                                                                AttributeNotRecognized,
                                                                                AttributeNotSubscribed,
                                                                                FederateInternalError)
{
  if (attributeReceived)
    attributeReceived(theObject, theAttributeValues);
}

@method
void reflectAttributeValues(ObjectInstanceHandle theObject,
                            AttributeHandleValueMap const& theAttributeValues,
                            VariableLengthData const& theUserSuppliedTag,
                            OrderType sentOrder,
                            TransportationType theType,
                            LogicalTime const& theTime,
                            OrderType receivedOrder) throw(ObjectInstanceNotKnown,
                                                            AttributeNotRecognized,
                                                            AttributeNotSubscribed,
                                                            FederateInternalError)
{
  if (attributeReceived)
    attributeReceived(theObject, theAttributeValues);
}

@method
std::wstring variableLengthDataToWstring(const rti1516::VariableLengthData& variableLengthData)
{
  if (!variableLengthData.size())
    return std::wstring();
  return std::wstring((const wchar_t*)variableLengthData.data(),
                      variableLengthData.size() / sizeof(std::wstring::value_type));
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                        ParameterHandleValueMap const& theParameterValues,
                        VariableLengthData const& theUserSuppliedTag,
                        OrderType sentOrder,
                        TransportationType theType) throw(InteractionClassNotRecognized,
                                                          InteractionParameterNotRecognized,
                                                          InteractionClassNotSubscribed,
                                                          FederateInternalError)
{
  if (interactionReceived)
    interactionReceived(theInteraction, theParameterValues);
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                        ParameterHandleValueMap const& theParameterValues,
                        VariableLengthData const& theUserSuppliedTag,
                        OrderType sentOrder,
                        TransportationType theType,
                        RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized,
                                                                            InteractionParameterNotRecognized,
                                                                            InteractionClassNotSubscribed,
                                                                            FederateInternalError)
{
  if (interactionReceived)
    interactionReceived(theInteraction, theParameterValues);
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                        ParameterHandleValueMap const& theParameterValues,
                        VariableLengthData const& theUserSuppliedTag,
                        OrderType sentOrder,
                        TransportationType theType,
                        LogicalTime const& theTime,
                        OrderType receivedOrder) throw(InteractionClassNotRecognized,
                                                      InteractionParameterNotRecognized,
                                                      InteractionClassNotSubscribed,
                                                      FederateInternalError)
{
  if (interactionReceived)
    interactionReceived(theInteraction, theParameterValues);
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                        ParameterHandleValueMap const& theParameterValues,
                        VariableLengthData const& theUserSuppliedTag,
                        OrderType sentOrder,
                        TransportationType theType,
                        LogicalTime const& theTime,
                        OrderType receivedOrder,
                        RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized,
                                                                            InteractionParameterNotRecognized,
                                                                            InteractionClassNotSubscribed,
                                                                            FederateInternalError)
{
  if (interactionReceived)
    interactionReceived(theInteraction, theParameterValues);
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                        ParameterHandleValueMap const& theParameterValues,
                        VariableLengthData const& theUserSuppliedTag,
                        OrderType sentOrder,
                        TransportationType theType,
                        LogicalTime const& theTime,
                        OrderType receivedOrder,
                        MessageRetractionHandle theHandle) throw(InteractionClassNotRecognized,
                                                                InteractionParameterNotRecognized,
                                                                InteractionClassNotSubscribed,
                                                                InvalidLogicalTime,
                                                                FederateInternalError)
{
  if (interactionReceived)
    interactionReceived(theInteraction, theParameterValues);
}

@method
void receiveInteraction(InteractionClassHandle theInteraction,
                        ParameterHandleValueMap const& theParameterValues,
                        VariableLengthData const& theUserSuppliedTag,
                        OrderType sentOrder,
                        TransportationType theType,
                        LogicalTime const& theTime,
                        OrderType receivedOrder,
                        MessageRetractionHandle theHandle,
                        RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized,
                                                                            InteractionParameterNotRecognized,
                                                                            InteractionClassNotSubscribed,
                                                                            InvalidLogicalTime,
                                                                            FederateInternalError)
{
  if (interactionReceived)
    interactionReceived(theInteraction, theParameterValues);
}

@method
void removeObjectInstance(ObjectInstanceHandle theObject,
                          VariableLengthData const& theUserSuppliedTag,
                          OrderType sentOrder) throw(ObjectInstanceNotKnown, FederateInternalError)
{
}

@method
void removeObjectInstance(ObjectInstanceHandle theObject,
                          VariableLengthData const& theUserSuppliedTag,
                          OrderType sentOrder,
                          LogicalTime const& theTime,
                          OrderType receivedOrder) throw(ObjectInstanceNotKnown, FederateInternalError)
{
}

@method
void removeObjectInstance(ObjectInstanceHandle theObject,
                          VariableLengthData const& theUserSuppliedTag,
                          OrderType sentOrder,
                          LogicalTime const& theTime,
                          OrderType receivedOrder,
                          MessageRetractionHandle theHandle) throw(ObjectInstanceNotKnown,
                                                                  InvalidLogicalTime,
                                                                  FederateInternalError)
{
}
