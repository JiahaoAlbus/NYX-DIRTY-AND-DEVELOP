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

import { getStoredLocale, translate } from "./i18nCore";

export function featureReasonText(status: CapabilityStatus | null): string {
  const locale = getStoredLocale();
  if (!status) return translate("capabilities.notLoaded", undefined, locale);
  if (status === "disabled") return translate("capabilities.disabled", undefined, locale);
  if (status.startsWith("disabled_")) {
    const reason = status.slice("disabled_".length).replaceAll("_", " ");
    return translate("capabilities.disabledReason", { reason }, locale);
  }
  if (status === "mandatory") return translate("capabilities.mandatory", undefined, locale);
  if (status === "verified") return translate("capabilities.verified", undefined, locale);
  return translate("capabilities.status", { status }, locale);
}
