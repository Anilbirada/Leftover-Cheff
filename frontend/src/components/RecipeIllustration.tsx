import React from 'react';

interface Props {
  recipeId: string;
  cuisine?: string | null;
  title: string;
}

const PALETTES: Record<string, { bg: string; plate: string; accent1: string; accent2: string; herb: string }> = {
  rec_potato_tomato_curry: { bg: '#F7EFE4', plate: '#FFFBF5', accent1: '#D9532E', accent2: '#E8A838', herb: '#2D6A4F' },
  rec_cheesy_potato_onion_skillet: { bg: '#F5EFE6', plate: '#2F3632', accent1: '#F4B942', accent2: '#D9532E', herb: '#40916C' },
  rec_spiced_tomato_onion_rice: { bg: '#FAF0E6', plate: '#FFFFFF', accent1: '#C84B31', accent2: '#F3C663', herb: '#2D6A4F' },
  rec_cheesy_tomato_rice_bake: { bg: '#F9EFE5', plate: '#3E2723', accent1: '#F5B841', accent2: '#E05A47', herb: '#386641' },
  rec_crispy_rice_flour_pancakes: { bg: '#F2F5EC', plate: '#FFFDF9', accent1: '#E5B159', accent2: '#D96B27', herb: '#2B5B3F' },
  rec_coconut_milk_potato_curry: { bg: '#EDF4F0', plate: '#FFFFFF', accent1: '#F2E8CF', accent2: '#E09F3E', herb: '#2D6A4F' },
  rec_garlic_butter_pasta: { bg: '#FBF4E8', plate: '#FFFFFF', accent1: '#E9C46A', accent2: '#F4A261', herb: '#2A9D8F' },
  rec_chickpea_spinach_tomato_stew: { bg: '#EEF4ED', plate: '#FFFDF8', accent1: '#D95D39', accent2: '#E2A84B', herb: '#1B4332' },
  rec_masala_omelette: { bg: '#FCF3E6', plate: '#2B2D2F', accent1: '#F6BD60', accent2: '#E0533C', herb: '#2D6A4F' },
  rec_spring_onion_soy_fried_rice: { bg: '#EEF3EE', plate: '#263238', accent1: '#F4E3B2', accent2: '#9E472A', herb: '#40916C' },
  rec_peanut_garlic_rice_bowl: { bg: '#F7EFE6', plate: '#FFFDF7', accent1: '#C66B3D', accent2: '#E5B25D', herb: '#2D6A4F' },
  rec_creamy_dairy_potato_bake: { bg: '#F9F3E8', plate: '#FFFDF9', accent1: '#F3C15A', accent2: '#D9822B', herb: '#386641' },
};

export const RecipeIllustration: React.FC<Props> = ({ recipeId, cuisine, title }) => {
  const palette = PALETTES[recipeId] || {
    bg: '#F4EFE6',
    plate: '#FFFFFF',
    accent1: '#D4622A',
    accent2: '#E8B14B',
    herb: '#23473B',
  };

  return (
    <svg
      viewBox="0 0 400 200"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
      role="img"
      aria-label={`Culinary illustration for ${title}`}
    >
      <rect width="400" height="200" fill={palette.bg} />
      <circle cx="340" cy="35" r="70" fill={palette.accent2} opacity="0.14" />
      <circle cx="55" cy="165" r="60" fill={palette.herb} opacity="0.1" />

      {/* Serving Bowl / Skillet */}
      <ellipse cx="200" cy="108" rx="92" ry="66" fill="rgba(0,0,0,0.08)" />
      <ellipse cx="200" cy="102" rx="88" ry="62" fill={palette.plate} stroke="#E4DCCF" strokeWidth="3" />
      <ellipse cx="200" cy="102" rx="72" ry="48" fill={palette.accent1} opacity="0.88" />

      {/* Food Elements */}
      <circle cx="176" cy="92" r="14" fill={palette.accent2} />
      <circle cx="218" cy="88" r="12" fill={palette.accent2} />
      <circle cx="195" cy="116" r="13" fill={palette.accent2} />
      <circle cx="228" cy="112" r="10" fill="#FFF8EA" opacity="0.9" />
      <circle cx="166" cy="112" r="9" fill="#FFF8EA" opacity="0.9" />

      {/* Herb Garnish */}
      <path
        d="M190 95 C195 82, 210 82, 206 96 C202 106, 188 104, 190 95 Z"
        fill={palette.herb}
      />
      <path
        d="M204 102 C214 94, 224 102, 212 110 C204 114, 198 106, 204 102 Z"
        fill={palette.herb}
      />

      {cuisine && (
        <g transform="translate(295, 158)">
          <rect x="0" y="0" width="90" height="26" rx="13" fill="rgba(255,255,255,0.9)" />
          <text
            x="45"
            y="17"
            textAnchor="middle"
            fontSize="11"
            fontWeight="700"
            fill="#23473B"
            fontFamily="sans-serif"
          >
            {cuisine}
          </text>
        </g>
      )}
    </svg>
  );
};
