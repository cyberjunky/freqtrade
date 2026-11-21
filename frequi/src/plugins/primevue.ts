import '@fontsource/ibm-plex-sans/latin-400.css';
import '@fontsource/ibm-plex-sans/latin-500.css';
import '@fontsource/ibm-plex-sans/latin-600.css';
import '@fontsource/ibm-plex-mono/latin-400.css';
import '@fontsource/ibm-plex-mono/latin-500.css';
import '@fontsource/ibm-plex-mono/latin-600.css';
import '@/styles/tailwind.css';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

/**
 * The PrimeVue preset contains NO colours of its own: every value points at a
 * design token (CSS custom property) from `styles/tokens.css`. The tokens switch
 * between dark and light, so both PrimeVue colour schemes share one mapping.
 */
const v = (name: string) => `var(--ft-${name})`;

const ramp = (prefix: string) =>
  Object.fromEntries(
    [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map((k) => [k, v(`${prefix}-${k}`)]),
  );

const scheme = {
  surface: { 0: v('s-0'), ...ramp('s') },
  primary: {
    color: v('primary'),
    contrastColor: v('on-primary'),
    hoverColor: v('primary-hover'),
    activeColor: v('primary-hover'),
  },
  highlight: {
    background: v('selected'),
    focusBackground: v('selected'),
    color: v('text'),
    focusColor: v('text'),
  },
  mask: {
    background: v('mask'),
    color: v('text'),
  },
  formField: {
    background: v('panel'),
    disabledBackground: v('page'),
    filledBackground: v('page'),
    filledHoverBackground: v('page'),
    filledFocusBackground: v('page'),
    borderColor: v('border'),
    hoverBorderColor: v('idle'),
    focusBorderColor: v('primary'),
    invalidBorderColor: v('danger'),
    color: v('text'),
    disabledColor: v('muted'),
    placeholderColor: v('muted'),
    invalidPlaceholderColor: v('danger'),
    floatLabelColor: v('muted'),
    floatLabelFocusColor: v('primary'),
    floatLabelActiveColor: v('muted'),
    floatLabelInvalidColor: v('danger'),
    iconColor: v('muted'),
    shadow: 'none',
  },
  text: {
    color: v('text'),
    hoverColor: v('text'),
    mutedColor: v('muted'),
    hoverMutedColor: v('text-2'),
  },
  content: {
    background: v('panel'),
    hoverBackground: v('hover'),
    borderColor: v('border'),
    color: v('text'),
    hoverColor: v('text'),
  },
  overlay: {
    select: { background: v('panel'), borderColor: v('border'), color: v('text') },
    popover: { background: v('panel'), borderColor: v('border'), color: v('text') },
    modal: { background: v('panel'), borderColor: v('border'), color: v('text') },
  },
  list: {
    option: {
      focusBackground: v('hover'),
      selectedBackground: v('selected'),
      selectedFocusBackground: v('selected'),
      color: v('text'),
      focusColor: v('text'),
      selectedColor: v('text'),
      selectedFocusColor: v('text'),
      icon: { color: v('muted'), focusColor: v('text-2') },
    },
    optionGroup: { background: 'transparent', color: v('muted') },
  },
  navigation: {
    item: {
      focusBackground: v('hover'),
      activeBackground: v('selected'),
      color: v('text'),
      focusColor: v('text'),
      activeColor: v('text'),
      icon: { color: v('muted'), focusColor: v('text-2'), activeColor: v('text-2') },
    },
    submenuLabel: { background: 'transparent', color: v('muted') },
    submenuIcon: { color: v('muted'), focusColor: v('text-2'), activeColor: v('text-2') },
  },
};

/** Default button: panel background + border. */
const neutralButton = {
  background: v('panel'),
  hoverBackground: v('hover'),
  activeBackground: v('hover'),
  borderColor: v('border'),
  hoverBorderColor: v('idle'),
  activeBorderColor: v('idle'),
  color: v('text'),
  hoverColor: v('text'),
  activeColor: v('text'),
  focusRing: { color: v('primary'), shadow: 'none' },
};
const buttonScheme = {
  root: {
    secondary: neutralButton,
    contrast: neutralButton,
    danger: {
      background: v('danger-solid'),
      hoverBackground: v('danger-solid'),
      activeBackground: v('danger-solid'),
      borderColor: v('danger-solid'),
      hoverBorderColor: v('danger-solid'),
      activeBorderColor: v('danger-solid'),
      color: v('on-primary'),
      hoverColor: v('on-primary'),
      activeColor: v('on-primary'),
      focusRing: { color: v('danger'), shadow: 'none' },
    },
  },
  outlined: {
    secondary: {
      hoverBackground: v('hover'),
      activeBackground: v('hover'),
      borderColor: v('border'),
      color: v('text'),
    },
  },
  text: {
    secondary: { hoverBackground: v('hover'), activeBackground: v('hover'), color: v('text-2') },
  },
};

const FtTheme = definePreset(Aura, {
  primitive: {
    borderRadius: { none: '0', xs: '2px', sm: '3px', md: '4px', lg: '6px', xl: '6px' },
  },
  semantic: {
    transitionDuration: '0.12s',
    focusRing: {
      width: '2px',
      style: 'solid',
      color: v('primary'),
      offset: '3px',
      shadow: 'none',
    },
    disabledOpacity: '0.5',
    iconSize: '1rem',
    anchorGutter: '4px',
    primary: ramp('p'),
    formField: {
      paddingX: '10px',
      paddingY: '4px',
      sm: { fontSize: '12px', paddingX: '8px', paddingY: '2px' },
      lg: { fontSize: '13px', paddingX: '12px', paddingY: '6px' },
      borderRadius: '{border.radius.md}',
      focusRing: { width: '2px', style: 'solid', color: v('primary'), offset: '0', shadow: 'none' },
      transitionDuration: '{transition.duration}',
    },
    list: {
      padding: '4px',
      gap: '1px',
      header: { padding: '6px 8px 4px 8px' },
      option: { padding: '5px 9px', borderRadius: '{border.radius.md}' },
      optionGroup: { padding: '6px 9px', fontWeight: '600' },
    },
    content: { borderRadius: '{border.radius.lg}' },
    mask: { transitionDuration: '0.12s' },
    navigation: {
      list: { padding: '4px', gap: '1px' },
      item: { padding: '5px 9px', borderRadius: '{border.radius.md}', gap: '8px' },
      submenuLabel: { padding: '6px 9px', fontWeight: '600' },
      submenuIcon: { size: '0.875rem' },
    },
    overlay: {
      select: { borderRadius: '{border.radius.lg}', shadow: v('shadow') },
      popover: { borderRadius: '{border.radius.lg}', padding: '10px', shadow: v('shadow') },
      modal: { borderRadius: '{border.radius.lg}', padding: '18px', shadow: v('shadow') },
      navigation: { shadow: v('shadow') },
    },
    colorScheme: {
      light: scheme,
      dark: scheme,
    },
  },
  components: {
    button: {
      root: {
        borderRadius: '{border.radius.md}',
        gap: '6px',
        paddingX: '11px',
        paddingY: '4px',
        iconOnlyWidth: '30px',
        sm: { fontSize: '12px', paddingX: '8px', paddingY: '2px', iconOnlyWidth: '24px' },
        lg: { fontSize: '12.5px', paddingX: '12px', paddingY: '4px', iconOnlyWidth: '30px' },
        label: { fontWeight: '500' },
        raisedShadow: 'none',
      },
      colorScheme: { light: buttonScheme, dark: buttonScheme },
    },
    datatable: {
      colorScheme: {
        light: {
          root: { borderColor: v('border') },
          bodyCell: { selectedBorderColor: v('border') },
        },
        dark: {
          root: { borderColor: v('border') },
          bodyCell: { selectedBorderColor: v('border') },
        },
      },
      headerCell: {
        background: v('panel'),
        hoverBackground: v('hover'),
        selectedBackground: v('panel'),
        borderColor: v('border'),
        color: v('text-2'),
        hoverColor: v('text'),
        selectedColor: v('primary'),
        gap: '4px',
      },
      row: {
        background: 'transparent',
        hoverBackground: v('hover'),
        selectedBackground: v('selected'),
        color: v('text'),
        hoverColor: v('text'),
        selectedColor: v('text'),
        stripedBackground: 'transparent',
      },
      bodyCell: { borderColor: v('border') },
      footerCell: { background: v('panel'), borderColor: v('border'), color: v('text') },
      header: { background: v('panel'), borderColor: v('border'), color: v('text') },
      footer: { background: v('panel'), borderColor: v('border'), color: v('text') },
      sortIcon: { color: v('muted'), hoverColor: v('text-2'), size: '0.75rem' },
    },
    dialog: {
      root: {
        background: v('panel'),
        borderColor: v('border'),
        color: v('text'),
        borderRadius: '{border.radius.lg}',
        shadow: v('shadow'),
      },
      title: { fontSize: '14px', fontWeight: '600' },
    },
    tooltip: {
      root: {
        maxWidth: '20rem',
        gutter: '4px',
        shadow: v('shadow'),
        padding: '5px 9px',
        borderRadius: '{border.radius.md}',
      },
      colorScheme: {
        light: { root: { background: v('text'), color: v('panel') } },
        dark: { root: { background: v('s-800'), color: v('text') } },
      },
    },
    toggleswitch: {
      root: { width: '30px', height: '16px', borderRadius: '16px', gap: '2px' },
      handle: { borderRadius: '50%', size: '12px' },
      colorScheme: {
        light: {
          root: {
            background: v('idle'),
            hoverBackground: v('idle'),
            checkedBackground: v('primary'),
            checkedHoverBackground: v('primary'),
          },
          handle: {
            background: v('on-primary'),
            hoverBackground: v('on-primary'),
            checkedBackground: v('on-primary'),
            checkedHoverBackground: v('on-primary'),
          },
        },
        dark: {
          root: {
            background: v('idle'),
            hoverBackground: v('idle'),
            checkedBackground: v('primary'),
            checkedHoverBackground: v('primary'),
          },
          handle: {
            background: v('on-primary'),
            hoverBackground: v('on-primary'),
            checkedBackground: v('on-primary'),
            checkedHoverBackground: v('on-primary'),
          },
        },
      },
    },
  },
});

export { PrimeVue, FtTheme, ToastService };
