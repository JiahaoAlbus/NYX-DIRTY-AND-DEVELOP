export type CapabilityStatus = "enabled" | "disabled" | "mandatory" | "verified" | string;

export type ModuleFeatures = Record<string, Record<string, CapabilityStatus>>;

export interface Capabilities {
  modules: string[];
  module_features: ModuleFeatures;
  endpoints?: string[];
  assets?: unknown[];
  exchange_pairs?: unknown[];
}

export function hasModule(caps: Capabilities | null, moduleName: string): boolean {
  if (!caps) return false;
  if (!Array.isArray(caps.modules)) return false;
  return caps.modules.includes(moduleName);
}

export function featureStatus(
  caps: Capabilities | null,
  moduleName: string,
  featureName: string,
): CapabilityStatus | null {
  if (!caps) return null;
  const moduleFeatures = caps.module_features?.[moduleName];
  if (!moduleFeatures) return null;
  const status = moduleFeatures[featureName];
  return typeof status === "string" ? status : null;
}

export function isFeatureEnabled(caps: Capabilities | null, moduleName: string, featureName: string): boolean {
  const status = featureStatus(caps, moduleName, featureName);
  if (!status) return false;
  if (status === "disabled") return false;
  if (status.startsWith("disabled_")) return false;
  return true;
}

export function isModuleUsable(caps: Capabilities | null, moduleName: string): boolean {
  if (!caps) return false;
  if (!hasModule(caps, moduleName)) return false;
  return typeof caps.module_features?.[moduleName] === "object";
}

export function featureReasonText(status: CapabilityStatus | null): string {
  if (!status) return "Capabilities not loaded yet.";
  if (status === "disabled") return "Disabled by backend capabilities.";
  if (status.startsWith("disabled_")) return `Disabled: ${status.slice("disabled_".length).replaceAll("_", " ")}.`;
  if (status === "mandatory") return "Mandatory for this environment.";
  if (status === "verified") return "Verified in this environment.";
  return `Capability status: ${status}`;
}
