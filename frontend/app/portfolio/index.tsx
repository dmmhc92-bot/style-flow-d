import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import EmptyState from '../../components/EmptyState';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

export default function PortfolioScreen() {
  const router = useRouter();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    loadPortfolio();
  }, []);
  
  const loadPortfolio = async () => {
    setLoading(true);
    try {
      const response = await api.get('/portfolio');
      setImages(response.data);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const onRefresh = async () => {
    setRefreshing(true);
    await loadPortfolio();
    setRefreshing(false);
  };
  
  const pickImage = async (useCamera: boolean) => {
    try {
      setUploading(true);
      
      let result;
      if (useCamera) {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          Alert.alert('Permission Required', 'Please allow camera access');
          setUploading(false);
          return;
        }
        result = await ImagePicker.launchCameraAsync({
          allowsEditing: true,
          aspect: [4, 3],
          quality: 0.7,
          base64: true,
        });
      } else {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          Alert.alert('Permission Required', 'Please allow photo library access');
          setUploading(false);
          return;
        }
        result = await ImagePicker.launchImagePickerAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [4, 3],
          quality: 0.7,
          base64: true,
        });
      }
      
      if (!result.canceled && result.assets[0].base64) {
        await uploadImage(`data:image/jpeg;base64,${result.assets[0].base64}`);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to select image');
    } finally {
      setUploading(false);
    }
  };
  
  const uploadImage = async (base64Image: string) => {
    try {
      await api.post('/portfolio', { image: base64Image });
      await loadPortfolio();
      Alert.alert('Success', 'Image added to portfolio');
    } catch (error) {
      Alert.alert('Error', 'Failed to upload image');
    }
  };
  
  const handleAddPhoto = () => {
    Alert.alert(
      'Add Photo',
      'Choose an option',
      [
        { text: 'Take Photo', onPress: () => pickImage(true) },
        { text: 'Choose from Library', onPress: () => pickImage(false) },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };
  
  const handleDeleteImage = (imageId: string) => {
    Alert.alert(
      'Delete Image',
      'Are you sure you want to remove this image from your portfolio?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/portfolio/${imageId}`);
              setImages(images.filter((img: any) => img.id !== imageId));
            } catch (error) {
              Alert.alert('Error', 'Failed to delete image');
            }
          },
        },
      ]
    );
  };
  
  const renderImage = ({ item }: any) => (
    <TouchableOpacity
      style={styles.imageCard}
      onLongPress={() => handleDeleteImage(item.id)}
      activeOpacity={0.8}
    >
      <View style={styles.imagePlaceholder}>
        <Ionicons name="image" size={40} color={Colors.accent} />
        <Text style={styles.imageText}>Portfolio Image</Text>
      </View>
      <TouchableOpacity
        style={styles.deleteButton}
        onPress={() => handleDeleteImage(item.id)}
      >
        <Ionicons name="trash-outline" size={16} color={Colors.error} />
      </TouchableOpacity>
    </TouchableOpacity>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Portfolio</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={handleAddPhoto}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator size="small" color={Colors.accent} />
          ) : (
            <Ionicons name="add" size={24} color={Colors.accent} />
          )}
        </TouchableOpacity>
      </View>
      
      <FlatList
        data={images}
        renderItem={renderImage}
        keyExtractor={(item: any) => item.id}
        numColumns={2}
        contentContainerStyle={styles.grid}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.accent} />
        }
        ListEmptyComponent={
          loading ? null : (
            <EmptyState
              icon="images-outline"
              title="Build Your Portfolio"
              description="Showcase your best work with before & after photos"
              actionLabel="Add Photo"
              onAction={handleAddPhoto}
            />
          )
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  addButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  grid: {
    padding: Spacing.screenPadding,
  },
  imageCard: {
    width: '48%',
    aspectRatio: 1,
    margin: '1%',
    borderRadius: Spacing.radiusMedium,
    overflow: 'hidden',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundCard,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  deleteButton: {
    position: 'absolute',
    top: Spacing.sm,
    right: Spacing.sm,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.error,
  },
});