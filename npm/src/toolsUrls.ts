import { URL_PROTOCOLS } from "./constants.js";
import { ToolError } from "./errors.js";
import type { ToolDeps, ToolHandlers } from "./toolTypes.js";
import { type TransformArg, toSdkTransform } from "./transform.js";

const assertAbsolute = (url: string): void => {
  if (!URL.canParse(url) || !URL_PROTOCOLS.has(new URL(url).protocol)) {
    throw new ToolError(`Not an absolute http(s) URL: ${JSON.stringify(url)}`);
  }
};

interface DeliveryUrlArgs {
  url: string;
  transform?: TransformArg;
}

interface SignedUrlArgs extends DeliveryUrlArgs {
  asset_id: string;
  expires_in_seconds: number;
}

export const urlTools = ({ client }: ToolDeps): ToolHandlers => ({
  build_delivery_url: ({ url, transform }: DeliveryUrlArgs) => {
    assertAbsolute(url);
    return { url: client.url(url, toSdkTransform(transform)) };
  },

  /**
   * Signs the asset and expiry only, then adds the transform to the signed URL.
   * `signedUrl()` in the Node SDK also signs transform values, and the live API
   * rejects those links: it verifies `"{id}:{exp}"`, as its reference specifies.
   */
  build_signed_url: ({ asset_id, url, expires_in_seconds, transform }: SignedUrlArgs) => {
    assertAbsolute(url);
    const signed = client.signedUrl({ id: asset_id, url }, { expiresIn: expires_in_seconds });
    return { url: client.url(signed, toSdkTransform(transform)) };
  },
});
