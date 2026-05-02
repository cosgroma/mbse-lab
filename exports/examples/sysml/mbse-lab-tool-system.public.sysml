// Generated from a Flexo SysML v2 REST export.
// Project: MBSE Lab Tool System Fixture
// Commit: mbse-lab-commit-1

package MBSE_Lab_Tool_System {
  package Stakeholders_and_Concerns {
    item def FirstTimeLocalUser;
    item def ModelAuthor;
    item def Maintainer;
    item def ReleasePublisher;
    item def FutureAgent;
  }
  package Landed_Feature_Requirements {
    requirement def BootstrapLocalLab;
    requirement def ManageLocalServices;
    requirement def PreservePrivateModelBoundary;
    requirement def ProvideSnapshotBridge;
    requirement def RenderConservativeSysMLSubset;
    requirement def CreateFirstModelEndToEnd;
    requirement def CollectRedactedDiagnostics;
    requirement def ProtectShareSafety;
    requirement def SupportDeterministicValidation;
    requirement def DocumentSupportedOperations;
  }
  package Architecture {
    part def MBSELabToolingRepo {
      part commandLineInterface;
      part flexoEnvironmentManager;
      part flexoSysONBridge;
      part diagnosticsCollector;
      part dockerDeployment;
      part privateModelWorkspace;
      part verificationHarness;
    }
  }
  package Workflows {
    action def BootstrapWorkflow;
    action def FirstModelWorkflow;
    action def FlexoToSysONSnapshotWorkflow;
    action def DiagnosticsWorkflow;
    action def ReleaseValidationWorkflow;
  }
  package Verification {
    action def DeterministicCheckSuite;
    action def LiveServiceEvalSuite;
    action def ShareSafetyCheck;
    action def DeploymentVerificationCheck;
    action def DocumentationCheck;
  }
}
