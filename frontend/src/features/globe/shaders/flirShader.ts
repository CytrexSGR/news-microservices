export const FLIR_FRAGMENT_SHADER = `
  uniform sampler2D colorTexture;
  in vec2 v_textureCoordinates;

  void main() {
    vec4 color = texture(colorTexture, v_textureCoordinates);
    float luminance = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    // White-hot FLIR palette
    vec3 flir;
    if (luminance < 0.33) {
      flir = mix(vec3(0.0, 0.0, 0.1), vec3(0.5, 0.0, 0.5), luminance * 3.0);
    } else if (luminance < 0.66) {
      flir = mix(vec3(0.5, 0.0, 0.5), vec3(1.0, 0.5, 0.0), (luminance - 0.33) * 3.0);
    } else {
      flir = mix(vec3(1.0, 0.5, 0.0), vec3(1.0, 1.0, 1.0), (luminance - 0.66) * 3.0);
    }
    out_FragColor = vec4(flir, 1.0);
  }
`;
