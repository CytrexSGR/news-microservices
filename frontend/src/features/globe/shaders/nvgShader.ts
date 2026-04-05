export const NVG_FRAGMENT_SHADER = `
  uniform sampler2D colorTexture;
  in vec2 v_textureCoordinates;

  void main() {
    vec4 color = texture(colorTexture, v_textureCoordinates);
    float luminance = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    // Green phosphor NVG look
    vec3 nvg = vec3(luminance * 0.1, luminance * 1.0, luminance * 0.15);
    // Add slight noise for authenticity
    float noise = fract(sin(dot(v_textureCoordinates, vec2(12.9898, 78.233))) * 43758.5453);
    nvg += vec3(noise * 0.03);
    // Slight vignette
    float dist = distance(v_textureCoordinates, vec2(0.5));
    float vignette = smoothstep(0.7, 0.4, dist);
    out_FragColor = vec4(nvg * vignette, 1.0);
  }
`;
