import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  View,
} from 'react-native';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  style?: any;
  textStyle?: any;
}

export default function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  icon,
  style,
  textStyle,
}: ButtonProps) {
  const getButtonStyle = () => {
    const baseStyle = [styles.button, styles[`button_${size}`]];
    
    if (variant === 'primary') {
      baseStyle.push(styles.buttonPrimary);
    } else if (variant === 'secondary') {
      baseStyle.push(styles.buttonSecondary);
    } else if (variant === 'outline') {
      baseStyle.push(styles.buttonOutline);
    }
    
    if (disabled || loading) {
      baseStyle.push(styles.buttonDisabled);
    }
    
    if (style) {
      baseStyle.push(style);
    }
    
    return baseStyle;
  };
  
  const getTextStyle = () => {
    const baseStyle = [styles.text, styles[`text_${size}`]];
    
    if (variant === 'primary') {
      baseStyle.push(styles.textPrimary);
    } else if (variant === 'secondary') {
      baseStyle.push(styles.textSecondary);
    } else if (variant === 'outline') {
      baseStyle.push(styles.textOutline);
    }
    
    if (textStyle) {
      baseStyle.push(textStyle);
    }
    
    return baseStyle;
  };
  
  return (
    <TouchableOpacity
      style={getButtonStyle()}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.85}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'outline' ? Colors.accent : Colors.textInverse} />
      ) : (
        <View style={styles.content}>
          {icon && <View style={styles.icon}>{icon}</View>}
          <Text style={getTextStyle()}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: Spacing.radiusMedium,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  button_small: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    minHeight: 36,
  },
  button_medium: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    minHeight: 48,
  },
  button_large: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    minHeight: 56,
  },
  buttonPrimary: {
    backgroundColor: Colors.accent,
  },
  buttonSecondary: {
    backgroundColor: Colors.primary,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  buttonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: Colors.accent,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    marginRight: 8,
  },
  text: {
    fontWeight: Typography.semibold,
    textAlign: 'center',
    letterSpacing: Typography.letterSpacingWide,
    textTransform: 'uppercase',
  },
  text_small: {
    fontSize: Typography.bodySmall,
  },
  text_medium: {
    fontSize: Typography.body,
  },
  text_large: {
    fontSize: Typography.h4,
  },
  textPrimary: {
    color: Colors.textInverse,
  },
  textSecondary: {
    color: Colors.text,
  },
  textOutline: {
    color: Colors.accent,
  },
});