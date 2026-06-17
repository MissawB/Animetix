import type { Meta, StoryObj } from '@storybook/react-vite';
import { Card } from './Card';
import React from 'react';

const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    padding: {
      control: { type: 'select' },
      options: ['none', 'sm', 'md', 'lg'],
    },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    padding: 'lg',
    children: (
      <div>
        <h3 className="text-xl font-bold mb-4">Titre de la carte</h3>
        <p className="text-gray-500">Ceci est un exemple de contenu affiché à l'intérieur de notre composant Card générique.</p>
      </div>
    ),
  },
};

export const NoPadding: Story = {
  args: {
    padding: 'none',
    children: (
      <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-32 rounded-[2rem] md:rounded-[3rem] flex items-center justify-center text-white font-bold">
        Contenu sans padding (idéal pour les images)
      </div>
    ),
  },
};
