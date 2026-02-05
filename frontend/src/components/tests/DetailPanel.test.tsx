import { render, screen } from '@testing-library/react';
import { DetailPanel } from '../DetailPanel';

const film = {
  id: 1,
  title: 'A New Hope',
  url: 'https://swapi.dev/api/films/1/',
  characters: [
    'https://swapi.dev/api/people/1/',
    'https://swapi.dev/api/people/2/',
  ],
  director: 'George Lucas',
} as any;

describe('DetailPanel', () => {
  it('does not render raw SWAPI url arrays in Details', () => {
    render(<DetailPanel resource={film} />);

    // não aparece url crua
    expect(screen.queryByText(/https:\/\/swapi\.dev\/api\/people\/1\//)).toBeNull();

    // aparece contagem
    expect(screen.getByText('2 items')).toBeInTheDocument();
  });

  it('still renders scalar fields', () => {
    render(<DetailPanel resource={film} />);
    expect(screen.getByText('George Lucas')).toBeInTheDocument();
  });

  it('does not duplicate title/name inside Details', () => {
    render(<DetailPanel resource={film} />);
    // "A New Hope" aparece no Basic Information
    expect(screen.getByText('A New Hope')).toBeInTheDocument();
    // mas não queremos um segundo "A New Hope" em Details via map
    // (não dá para garantir contagem exata sem um seletor, mas ao menos garante que não renderiza "title" como label)
    expect(screen.queryByText('Title')).toBeNull();
  });
});
