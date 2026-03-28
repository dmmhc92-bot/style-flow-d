import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

interface CredentialBadgeProps {
  isVerified?: boolean;
  licenseState?: string;
  certifications?: string[];
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
  onPress?: () => void;
}

/**
 * CredentialBadge - Displays stylist verification/license status
 * 
 * Features:
 * - Verified checkmark badge
 * - License state indicator
 * - Certification chips
 */
export const CredentialBadge: React.FC<CredentialBadgeProps> = ({
  isVerified = false,
  licenseState,
  certifications = [],
  size = 'medium',
  showDetails = false,
  onPress,
}) => {
  const iconSize = size === 'small' ? 12 : size === 'large' ? 20 : 16;
  const badgeSize = size === 'small' ? 20 : size === 'large' ? 32 : 24;
  
  if (!isVerified && !licenseState && certifications.length === 0) {
    return null;
  }

  const Badge = (
    <View style={styles.container}>
      {/* Verified Badge */}
      {isVerified && (
        <View style={[styles.verifiedBadge, { width: badgeSize, height: badgeSize }]}>
          <Ionicons name="checkmark-circle" size={iconSize} color={Colors.info} />
        </View>
      )}
      
      {/* License State Badge */}
      {licenseState && (
        <View style={styles.licenseBadge}>
          <Ionicons name="ribbon" size={iconSize - 2} color={Colors.vip} />
          <Text style={[styles.licenseText, size === 'small' && styles.smallText]}>
            {licenseState}
          </Text>
        </View>
      )}
      
      {/* Certification Chips (if showDetails) */}
      {showDetails && certifications.length > 0 && (
        <View style={styles.certifications}>
          {certifications.slice(0, 3).map((cert, index) => (
            <View key={index} style={styles.certChip}>
              <Text style={styles.certText}>{cert}</Text>
            </View>
          ))}
          {certifications.length > 3 && (
            <View style={styles.certChip}>
              <Text style={styles.certText}>+{certifications.length - 3}</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
        {Badge}
      </TouchableOpacity>
    );
  }

  return Badge;
};

/**
 * VerifiedBadgeInline - Compact verified checkmark for name lines
 */
export const VerifiedBadgeInline: React.FC<{ size?: number }> = ({ size = 16 }) => (
  <View style={styles.inlineBadge}>
    <Ionicons name="checkmark-circle" size={size} color={Colors.info} />
  </View>
);

/**
 * FeaturedBadge - Star badge for featured stylists
 */
export const FeaturedBadge: React.FC<{ size?: 'small' | 'medium' }> = ({ size = 'medium' }) => {
  const iconSize = size === 'small' ? 12 : 16;
  
  return (
    <View style={[styles.featuredBadge, size === 'small' && styles.featuredBadgeSmall]}>
      <Ionicons name="star" size={iconSize} color={Colors.vip} />
      <Text style={[styles.featuredText, size === 'small' && styles.smallText]}>
        Featured
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  verifiedBadge: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.info + '15',
    borderRadius: 12,
  },
  licenseBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.vip + '15',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  licenseText: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold as any,
    color: Colors.vip,
  },
  smallText: {
    fontSize: 10,
  },
  certifications: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: Spacing.xs,
  },
  certChip: {
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  certText: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontWeight: Typography.medium as any,
  },
  inlineBadge: {
    marginLeft: 4,
  },
  featuredBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.vip + '20',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  featuredBadgeSmall: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  featuredText: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold as any,
    color: Colors.vip,
  },
});

export default CredentialBadge;
